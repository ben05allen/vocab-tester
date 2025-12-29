from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .db import Database
from .quiz_screen import QuizScreen


class VocabTesterApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit")]

    def on_mount(self) -> None:
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
        yield QuizScreen(Database())

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"
