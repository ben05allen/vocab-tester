from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Input, Button, Label
from textual.reactive import reactive
from textual import work

from .config import Config
from .db import Database
from .edit_word_screen import EditWordScreen
from .tag_screen import TagSelectionScreen
from .models import Word
from .wsl_utils import set_ime_mode
from .text_utils import kanji_to_kana, is_answer_correct
from .audio_service import AudioService
from .quiz_session import QuizSession

_config_path = Path("settings.toml")
CONFIG = Config.from_file(_config_path)


class QuizScreen(Container):
    """The main quiz interface."""

    current_word = reactive(None)
    step = reactive("kana")  # kana -> meaning -> result

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        # Load default filter if set and valid
        default_filter = CONFIG.default_filter
        available_tags = self.db.get_tags() if hasattr(self.db, "get_tags") else []
        initial_tag = default_filter if default_filter in available_tags else None

        self.session = QuizSession(db, initial_tag)
        self.audio_service = AudioService()
        self.kana_answer = ""
        self.meaning_answer = ""
        self.full_info = ""

    @property
    def queue(self) -> list[int]:
        return self.session.queue

    @queue.setter
    def queue(self, val: list[int]) -> None:
        self.session.queue = val

    @property
    def question_data(self) -> Word | None:
        return self.session.current_word

    @question_data.setter
    def question_data(self, val: Word | None) -> None:
        self.session.current_word = val

    @property
    def current_tag_filter(self) -> str | None:
        return self.session.current_tag_filter

    @current_tag_filter.setter
    def current_tag_filter(self, val: str | None) -> None:
        self.session.current_tag_filter = val

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
                yield Button(
                    "Test Again",
                    variant="warning",
                    id="test_again_btn",
                    classes="hidden",
                )
                yield Button("Filter", variant="default", id="filter_btn")
                yield Button("Quit", variant="error", id="quit_btn")

    def on_mount(self) -> None:
        if self.session.current_tag_filter:
            self.query_one("#filter_label", Label).update(
                f"Filter: {self.session.current_tag_filter}"
            )

        self.next_question()

    def next_question(self) -> None:
        word = self.session.next_question()

        if not word:
            self.query_one("#sentence_label", Label).update(
                "No words found for this filter!"
            )
            self.query_one("#answer_input", Input).disabled = True
            return

        self.step = "kana"
        set_ime_mode(True)
        self.kana_answer = ""
        self.meaning_answer = ""
        self.full_info = ""

        self.query_one("#sentence_label", Label).update(word.japanese_sentence)
        self.query_one("#prompt_label", Label).update(
            f"Reading for: [white]{word.kanji_word}[/]"
        )

        inp = self.query_one("#answer_input", Input)
        inp.value = ""
        inp.disabled = False
        inp.focus()

        self.query_one("#result_message", Static).update("")
        self.query_one("#full_info", Static).update(self.full_info)
        self.query_one("#footer-buttons").styles.display = "none"
        self.query_one("#copy_btn").add_class("hidden")
        self.query_one("#audio_btn").add_class("hidden")
        self.query_one("#test_again_btn").add_class("hidden")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.session.current_word:
            return

        val = event.value.strip()

        if self.step == "kana":
            self.kana_answer = val
            self.step = "meaning"
            set_ime_mode(False)
            self.query_one("#prompt_label", Label).update(
                f"Meaning of: [white]{self.session.current_word.kanji_word}[/]"
            )
            event.input.value = ""

        elif self.step == "meaning":
            self.meaning_answer = val
            self.show_results()

    def show_results(self) -> None:
        if not self.session.current_word:
            return

        self.step = "result"
        self.query_one("#answer_input", Input).disabled = True

        is_kana_correct = self.kana_answer == self.session.current_word.kana_word
        is_meaning_correct = is_answer_correct(
            self.meaning_answer, self.session.current_word.english_word
        )
        overall_correct = is_kana_correct and is_meaning_correct

        # Record result
        self.session.record_result(overall_correct)
        if hasattr(self.app, "update_score"):
            self.app.update_score(overall_correct)  # type: ignore

        if overall_correct:
            result_text = "[green bold]Correct![/]"
        else:
            parts = []
            if not is_kana_correct:
                parts.append(f"Reading: {self.session.current_word.kana_word}")
            if not is_meaning_correct:
                parts.append(f"Meaning: {self.session.current_word.english_word}")
            result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)

        self.query_one("#result_message", Static).update(result_text)

        self.full_info = (
            f"Sentence: {self.session.current_word.english_sentence}\n"
            f"Kana: {kanji_to_kana(self.session.current_word.japanese_sentence)}\n"
            f"({self.session.current_word.kanji_word} = {self.session.current_word.kana_word} / {self.session.current_word.english_word})"
        )
        self.query_one("#full_info", Static).update(self.full_info)

        self.query_one("#footer-buttons").styles.display = "block"
        self.query_one("#copy_btn").remove_class("hidden")
        self.query_one("#audio_btn").remove_class("hidden")
        if not overall_correct:
            self.query_one("#test_again_btn").remove_class("hidden")
        else:
            self.query_one("#test_again_btn").add_class("hidden")
        self.query_one("#next_btn").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next_btn":
            self.next_question()
        elif event.button.id == "test_again_btn":
            self.test_again()
        elif event.button.id == "quit_btn":
            self.app.exit()
        elif event.button.id == "filter_btn":
            self.app.push_screen(TagSelectionScreen(self.db), self.on_filter_selected)
        elif event.button.id == "copy_btn":
            if self.session.current_word:
                self.app.copy_to_clipboard(self.session.current_word.japanese_sentence)
        elif event.button.id == "audio_btn":
            self.play_audio()

    def test_again(self) -> None:
        if self.session.current_word and self.session.current_word.id is not None:
            self.session.queue.insert(0, self.session.current_word.id)
            self.next_question()

    @work(exclusive=True, thread=True)
    def play_audio(self) -> None:
        if (
            not self.session.current_word
            or not self.session.current_word.japanese_sentence
        ):
            return
        self._generate_and_play_audio(self.session.current_word.japanese_sentence)

    def _generate_and_play_audio(self, sentence: str) -> None:
        try:
            self.audio_service.play_japanese_sentence(sentence)
        except Exception as e:
            self.app.notify(f"Error playing audio: {e}", severity="error")

    def on_filter_selected(self, tag: str | None) -> None:
        if tag is None:
            return

        self.session.set_tag_filter(tag if tag else None)

        label_text = (
            f"Filter: {self.session.current_tag_filter}"
            if self.session.current_tag_filter
            else "Filter: All"
        )
        self.query_one("#filter_label", Label).update(label_text)

        # Reset UI state (hide result buttons, clear inputs)
        self.query_one("#answer_input", Input).disabled = False
        self.query_one("#result_message", Static).update("")
        self.query_one("#full_info", Static).update("")
        self.query_one("#footer-buttons").styles.display = "none"
        self.query_one("#copy_btn").add_class("hidden")
        self.query_one("#audio_btn").add_class("hidden")

        self.next_question()

    def action_edit_word(self) -> None:
        if (
            self.step == "result"
            and self.session.current_word
            and self.session.current_word.id
        ):
            self.app.push_screen(  # type: ignore
                EditWordScreen(self.db, self.session.current_word.id),
                self.on_edit_word_done,
            )

    def on_edit_word_done(self, changed: bool) -> None:
        if changed and self.session.current_word and self.session.current_word.id:
            # Reload data
            word_id = self.session.current_word.id
            new_data = self.db.get_word(word_id)
            if new_data:
                self.session.current_word = new_data

                # Refresh display
                self.full_info = (
                    f"Sentence: {self.session.current_word.english_sentence}\n"
                    f"Kana: {kanji_to_kana(self.session.current_word.japanese_sentence)}\n"
                    f"({self.session.current_word.kanji_word} = {self.session.current_word.kana_word} / {self.session.current_word.english_word})"
                )
                self.query_one("#full_info", Static).update(self.full_info)
                self.query_one("#sentence_label", Label).update(
                    self.session.current_word.japanese_sentence
                )

                # Re-calculate result message
                is_kana_correct = (
                    self.kana_answer == self.session.current_word.kana_word
                )
                is_meaning_correct = is_answer_correct(
                    self.meaning_answer, self.session.current_word.english_word
                )
                overall_correct = is_kana_correct and is_meaning_correct

                if overall_correct:
                    result_text = "[green bold]Correct![/]"
                    self.query_one("#test_again_btn").add_class("hidden")
                else:
                    parts = []
                    if not is_kana_correct:
                        parts.append(f"Reading: {self.session.current_word.kana_word}")
                    if not is_meaning_correct:
                        parts.append(
                            f"Meaning: {self.session.current_word.english_word}"
                        )
                    result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)
                    self.query_one("#test_again_btn").remove_class("hidden")

                self.query_one("#result_message", Static).update(result_text)
