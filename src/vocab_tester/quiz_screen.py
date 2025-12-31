from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Input, Button, Label
from textual.reactive import reactive
from .db import Database
from .edit_word_screen import EditWordScreen


class QuizScreen(Container):
    """The main quiz interface."""

    current_word = reactive(None)
    step = reactive("kana")  # kana -> meaning -> result

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.queue = []
        self.question_data = None
        self.kana_answer = ""
        self.meaning_answer = ""

    def compose(self) -> ComposeResult:
        with Container(id="container"):
            yield Label("", id="sentence_label", classes="sentence")
            yield Label("", id="prompt_label", classes="prompt")
            yield Input(placeholder="Type answer here...", id="answer_input")

            # Result area
            yield Static("", id="result_message")
            yield Static("", id="full_info", classes="translation")

            with Horizontal(id="footer-buttons"):
                yield Button("Next", variant="primary", id="next_btn")
                yield Button("Quit", variant="error", id="quit_btn")

    def on_mount(self) -> None:
        self.next_question()

    def next_question(self) -> None:
        while len(self.queue) < 10:
            word = self.db.get_random_word()
            if not word:
                break
            self.queue.append(word)

        if not self.queue:
            self.query_one("#sentence_label", Label).update("No words in database!")
            self.query_one("#answer_input", Input).disabled = True
            return

        self.question_data = self.queue.pop(0)
        # question_data: (id, kanji, sentence, kana, meaning, eng_sentence, tag)
        (
            _,
            self.kanji,
            self.sentence,
            self.kana,
            self.meaning,
            self.eng_sentence,
            self.tag,
        ) = self.question_data

        self.step = "kana"
        self.kana_answer = ""
        self.meaning_answer = ""

        self.query_one("#sentence_label", Label).update(self.sentence)
        self.query_one("#prompt_label", Label).update(f"Reading for: {self.kanji}")

        inp = self.query_one("#answer_input", Input)
        inp.value = ""
        inp.disabled = False
        inp.focus()

        self.query_one("#result_message", Static).update("")
        self.query_one("#full_info", Static).update("")
        self.query_one("#footer-buttons").styles.display = "none"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()

        if self.step == "kana":
            self.kana_answer = val
            self.step = "meaning"
            self.query_one("#prompt_label", Label).update(f"Meaning of: {self.kanji}")
            event.input.value = ""

        elif self.step == "meaning":
            self.meaning_answer = val
            self.show_results()

    def show_results(self) -> None:
        self.step = "result"
        self.query_one("#answer_input", Input).disabled = True

        is_kana_correct = self.kana_answer == self.kana
        # Simple containment check for meaning or exact match? Let's do simple for now.
        is_meaning_correct = self.meaning_answer.lower() == self.meaning.lower()

        overall_correct = is_kana_correct and is_meaning_correct

        # Record result (logic in db can be expanded)
        if self.question_data:
            self.db.record_result(self.question_data[0], overall_correct)
            if hasattr(self.app, "update_score"):
                self.app.update_score(overall_correct)

            if not overall_correct:
                # Re-queue the word at different positions to practice again
                self.queue.insert(2, self.question_data)
                self.queue.insert(5, self.question_data)

        result_text = ""
        if overall_correct:
            result_text = "[green bold]Correct![/]"
        else:
            parts = []
            if not is_kana_correct:
                parts.append(f"Reading: {self.kana}")
            if not is_meaning_correct:
                parts.append(f"Meaning: {self.meaning}")
            result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)

        self.query_one("#result_message", Static).update(result_text)

        full_info = f"Sentence: {self.eng_sentence}\n({self.kanji} = {self.kana} / {self.meaning})"
        self.query_one("#full_info", Static).update(full_info)

        self.query_one("#footer-buttons").styles.display = "block"
        self.query_one("#next_btn").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next_btn":
            self.next_question()
        elif event.button.id == "quit_btn":
            self.app.exit()

    def action_edit_word(self) -> None:
        if self.step == "result" and self.question_data:
            self.app.push_screen(
                EditWordScreen(self.db, self.question_data[0]), self.on_edit_word_done
            )

    def on_edit_word_done(self, changed: bool) -> None:
        if changed and self.question_data:
            # Reload data
            word_id = self.question_data[0]
            new_data = self.db.get_word(word_id)
            if new_data:
                self.question_data = new_data
                (
                    _,
                    self.kanji,
                    self.sentence,
                    self.kana,
                    self.meaning,
                    self.eng_sentence,
                    self.tag,
                ) = new_data

                # Refresh display
                full_info = f"Sentence: {self.eng_sentence}\n({self.kanji} = {self.kana} / {self.meaning})"
                self.query_one("#full_info", Static).update(full_info)
                self.query_one("#sentence_label", Label).update(self.sentence)

                # Re-calculate result message
                is_kana_correct = self.kana_answer == self.kana
                is_meaning_correct = self.meaning_answer.lower() == self.meaning.lower()
                overall_correct = is_kana_correct and is_meaning_correct

                result_text = ""
                if overall_correct:
                    result_text = "[green bold]Correct![/]"
                else:
                    parts = []
                    if not is_kana_correct:
                        parts.append(f"Reading: {self.kana}")
                    if not is_meaning_correct:
                        parts.append(f"Meaning: {self.meaning}")
                    result_text = "[red bold]Incorrect.[/] " + ", ".join(parts)

                self.query_one("#result_message", Static).update(result_text)
