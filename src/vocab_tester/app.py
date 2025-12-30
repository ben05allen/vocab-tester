from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .db import Database
from .quiz_screen import QuizScreen
from .add_word_screen import AddWordScreen


class VocabTesterApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_word", "Add Word"),
        ("e", "edit_word", "Edit Word"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.db = Database()
        self.score_correct = 0
        self.score_total = 0
        self.update_score_display()

    def update_score_display(self) -> None:
        self.sub_title = f"Score: {self.score_correct}/{self.score_total}"

    def update_score(self, is_correct: bool) -> None:
        self.score_total += 1
        if is_correct:
            self.score_correct += 1
        self.update_score_display()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        # We initialized self.db in on_mount, but compose runs before on_mount in some lifecycle versions or concurrently?
        # Actually compose runs first. So on_mount is too late for compose if we use self.db there.
        # But wait, in the original code: yield QuizScreen(Database()) was in compose.
        # I'll stick to creating it in compose or __init__.
        # Let's use __init__ or just create it here.
        yield QuizScreen(Database())

    def action_edit_word(self) -> None:
        self.query_one(QuizScreen).action_edit_word()

    def action_add_word(self) -> None:
        self.push_screen(AddWordScreen(Database()))

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"
