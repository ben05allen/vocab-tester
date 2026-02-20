import os
import re
import subprocess
import tempfile
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Input, Button, Label
from textual.reactive import reactive
from textual import work
from .db import Database
from .edit_word_screen import EditWordScreen
from .tag_screen import TagSelectionScreen
from .models import Word
from .wsl_utils import set_ime_mode


def normalize_text(text: str) -> str:
    """
    Normalizes text by converting to lowercase and removing all spaces and punctuation.
    """
    # Remove all characters that are not letters or numbers
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]", "", normalized)
    return normalized


def is_answer_correct(user_answer: str, correct_answers_str: str) -> bool:
    """
    Checks if the user's answer matches any of the semicolon-separated correct answers,
    ignoring case, spaces, and punctuation.
    """
    user_normalized = normalize_text(user_answer)
    if not user_normalized and user_answer.strip():
        # If the user typed something that becomes empty after normalization (e.g. just punctuation)
        # we just fail.
        # But usually, if they typed "...", it shouldn't match "word".
        return False

    correct_list = [a.strip() for a in correct_answers_str.split(";")]
    for correct in correct_list:
        if user_normalized == normalize_text(correct):
            return True
    return False


class QuizScreen(Container):
    """The main quiz interface."""

    current_word = reactive(None)
    step = reactive("kana")  # kana -> meaning -> result

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.queue: list[int] = []
        self.question_data: Word | None = None
        self.kana_answer = ""
        self.meaning_answer = ""
        self.current_tag_filter = None

    def compose(self) -> ComposeResult:
        with Container(id="container"):
            yield Label("Filter: All", id="filter_label")
            with Horizontal(id="sentence_row"):
                yield Label("", id="sentence_label", classes="sentence")
                yield Button("📔", id="copy_btn", variant="default", classes="hidden")
                yield Button("🔊", id="audio_btn", variant="default", classes="hidden")
            yield Label("", id="prompt_label", classes="prompt")
            yield Input(placeholder="Type answer here...", id="answer_input")

            # Result area
            yield Static("", id="result_message")
            yield Static("", id="full_info", classes="translation")

            with Horizontal(id="footer-buttons"):
                yield Button("Next", variant="primary", id="next_btn")
                yield Button("Filter", variant="default", id="filter_btn")
                yield Button("Quit", variant="error", id="quit_btn")

    def on_mount(self) -> None:
        self.next_question()

    def next_question(self) -> None:
        needed = 10 - len(self.queue)
        if needed > 0:
            exclude_ids = list(self.queue)

            # 1. Fetch incorrect words first
            incorrect_ids = self.db.get_incorrect_word_ids(
                limit=needed,
                tag_filter=self.current_tag_filter,
                exclude_ids=exclude_ids,
            )
            self.queue.extend(incorrect_ids)

            needed -= len(incorrect_ids)
            if needed > 0:
                exclude_ids.extend(incorrect_ids)

                # 2. Fetch random words for the rest
                random_ids = self.db.get_random_word_ids(
                    limit=needed,
                    tag_filter=self.current_tag_filter,
                    exclude_ids=exclude_ids,
                )
                self.queue.extend(random_ids)

        if not self.queue:
            self.query_one("#sentence_label", Label).update(
                "No words found for this filter!"
            )
            self.query_one("#answer_input", Input).disabled = True
            return

        word_id = self.queue.pop(0)
        self.question_data = self.db.get_word(word_id)

        # If word not found (deleted?), skip
        if not self.question_data:
            self.next_question()
            return

        self.step = "kana"
        set_ime_mode(True)
        self.kana_answer = ""
        self.meaning_answer = ""

        self.query_one("#sentence_label", Label).update(
            self.question_data.japanese_sentence
        )
        self.query_one("#prompt_label", Label).update(
            f"Reading for: [white]{self.question_data.kanji_word}[/]"
        )

        inp = self.query_one("#answer_input", Input)
        inp.value = ""
        inp.disabled = False
        inp.focus()

        self.query_one("#result_message", Static).update("")
        self.query_one("#full_info", Static).update("")
        self.query_one("#footer-buttons").styles.display = "none"  # type: ignore
        self.query_one("#copy_btn").add_class("hidden")
        self.query_one("#audio_btn").add_class("hidden")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.question_data:
            return

        val = event.value.strip()

        if self.step == "kana":
            self.kana_answer = val
            self.step = "meaning"
            set_ime_mode(False)
            self.query_one("#prompt_label", Label).update(
                f"Meaning of: [white]{self.question_data.kanji_word}[/]"
            )
            event.input.value = ""

        elif self.step == "meaning":
            self.meaning_answer = val
            self.show_results()

    def show_results(self) -> None:
        if not self.question_data:
            return

        self.step = "result"
        self.query_one("#answer_input", Input).disabled = True

        is_kana_correct = self.kana_answer == self.question_data.kana_word
        # Validate meaning
        is_meaning_correct = is_answer_correct(
            self.meaning_answer, self.question_data.english_word
        )
        overall_correct = is_kana_correct and is_meaning_correct

        # Record result (logic in db can be expanded)
        if self.question_data.id:
            self.db.record_result(self.question_data.id, overall_correct)
            if hasattr(self.app, "update_score"):
                self.app.update_score(overall_correct)  # type: ignore

            # Re-queue the word at different positions to practice again
            # if not already in the queue a couple of times
            if not overall_correct and self.queue[1:].count(self.question_data.id) < 2:
                self.queue.insert(2, self.question_data.id)
                self.queue.insert(5, self.question_data.id)

        result_text = ""
        if overall_correct:
            result_text = "[green bold]Correct![/]"
        else:
            parts = []
            if not is_kana_correct:
                parts.append(f"Reading: {self.question_data.kana_word}")
            if not is_meaning_correct:
                parts.append(f"Meaning: {self.question_data.english_word}")
            result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)

        self.query_one("#result_message", Static).update(result_text)

        full_info = f"Sentence: {self.question_data.english_sentence}\n({self.question_data.kanji_word} = {self.question_data.kana_word} / {self.question_data.english_word})"
        self.query_one("#full_info", Static).update(full_info)

        self.query_one("#footer-buttons").styles.display = "block"
        self.query_one("#copy_btn").remove_class("hidden")
        self.query_one("#audio_btn").remove_class("hidden")
        self.query_one("#next_btn").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next_btn":
            self.next_question()
        elif event.button.id == "quit_btn":
            self.app.exit()
        elif event.button.id == "filter_btn":
            self.app.push_screen(TagSelectionScreen(self.db), self.on_filter_selected)
        elif event.button.id == "copy_btn":
            if self.question_data:
                self.app.copy_to_clipboard(self.question_data.japanese_sentence)
        elif event.button.id == "audio_btn":
            self.play_audio()

    @work(exclusive=True, thread=True)
    def play_audio(self) -> None:
        if not self.question_data or not self.question_data.japanese_sentence:
            return
        self._generate_and_play_audio(self.question_data.japanese_sentence)

    def _generate_and_play_audio(self, sentence: str) -> None:
        try:
            from gtts import gTTS

            # Generate audio
            tts = gTTS(sentence, lang="ja")

            # Create a temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name

            tts.save(temp_path)

            # Play audio
            subprocess.run(["mpg123", "-q", temp_path], check=False)

            # Cleanup
            os.remove(temp_path)

        except ImportError:
            self.app.notify(
                "gTTS not installed. Please run 'uv sync'.", severity="error"
            )
        except Exception as e:
            self.app.notify(f"Error playing audio: {e}", severity="error")

    def on_filter_selected(self, tag: str | None) -> None:
        if tag is None:
            # Cancelled, do nothing
            return

        # Tag is either a string or "" (empty string for All)
        self.current_tag_filter = tag if tag else None

        # Update label
        label_text = (
            f"Filter: {self.current_tag_filter}"
            if self.current_tag_filter
            else "Filter: All"
        )
        self.query_one("#filter_label", Label).update(label_text)

        # Clear queue and get new questions
        self.queue.clear()

        # Reset UI state (hide result buttons, clear inputs)
        self.query_one("#answer_input", Input).disabled = False
        self.query_one("#result_message", Static).update("")
        self.query_one("#full_info", Static).update("")
        self.query_one("#footer-buttons").styles.display = "none"  # type: ignore
        self.query_one("#copy_btn").add_class("hidden")
        self.query_one("#audio_btn").add_class("hidden")

        self.next_question()

    def action_edit_word(self) -> None:
        if self.step == "result" and self.question_data and self.question_data.id:
            self.app.push_screen(  # type: ignore
                EditWordScreen(self.db, self.question_data.id), self.on_edit_word_done
            )

    def on_edit_word_done(self, changed: bool) -> None:
        if changed and self.question_data and self.question_data.id:
            # Reload data
            word_id = self.question_data.id
            new_data = self.db.get_word(word_id)
            if new_data:
                self.question_data = new_data

                # Refresh display
                full_info = f"Sentence: {self.question_data.english_sentence}\n({self.question_data.kanji_word} = {self.question_data.kana_word} / {self.question_data.english_word})"
                self.query_one("#full_info", Static).update(full_info)
                self.query_one("#sentence_label", Label).update(
                    self.question_data.japanese_sentence
                )

                # Re-calculate result message
                is_kana_correct = self.kana_answer == self.question_data.kana_word
                is_meaning_correct = is_answer_correct(
                    self.meaning_answer, self.question_data.english_word
                )
                overall_correct = is_kana_correct and is_meaning_correct

                result_text = ""
                if overall_correct:
                    result_text = "[green bold]Correct![/]"
                else:
                    parts = []
                    if not is_kana_correct:
                        parts.append(f"Reading: {self.question_data.kana_word}")
                    if not is_meaning_correct:
                        parts.append(f"Meaning: {self.question_data.english_word}")
                    result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)

                self.query_one("#result_message", Static).update(result_text)
