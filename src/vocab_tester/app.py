from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from .db import Database
from .quiz_screen import QuizScreen


class VocabTesterApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield QuizScreen(Database())

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
