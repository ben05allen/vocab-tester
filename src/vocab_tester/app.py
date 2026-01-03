import shutil
import subprocess
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

    def copy_to_clipboard(self, text: str) -> None:
        """Override to support WSL2 clipboard with UTF-8 support."""
        # 1. Try PowerShell (Best for UTF-8/Japanese support)
        if shutil.which("powershell.exe"):
            try:
                # Use MemoryStream to read bytes from stdin safely
                full_command = (
                    "$ms = New-Object System.IO.MemoryStream; "
                    "[Console]::OpenStandardInput().CopyTo($ms); "
                    "$text = [System.Text.Encoding]::UTF8.GetString($ms.ToArray()); "
                    "Set-Clipboard -Value $text"
                )

                process = subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        full_command,
                    ],
                    stdin=subprocess.PIPE,
                    close_fds=True,
                )
                process.communicate(input=text.encode("utf-8"))
                if process.returncode == 0:
                    self.notify("Copied to clipboard (WSL)!")
                    return
            except Exception:
                pass

        # 2. Try clip.exe (Standard WSL tool, but often fails with non-ASCII)
        if shutil.which("clip.exe"):
            try:
                process = subprocess.Popen(
                    ["clip.exe"], stdin=subprocess.PIPE, close_fds=True
                )
                process.communicate(input=text.encode("utf-8"))
                if process.returncode == 0:
                    self.notify("Copied to clipboard (WSL-clip)!")
                    return
            except Exception:
                pass

        # 3. Final Fallback to default behavior
        try:
            super().copy_to_clipboard(text)
            self.notify("Copied to clipboard!")
        except Exception as e:
            self.notify(f"Copy failed: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield QuizScreen(Database())

    def action_edit_word(self) -> None:
        self.query_one(QuizScreen).action_edit_word()

    def action_add_word(self) -> None:
        self.push_screen(AddWordScreen(Database()))

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"
