from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from .db import Database


class AddWordScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Add New Word", id="add_word_title"),
            Vertical(
                Label("Kanji Word"),
                Input(placeholder="e.g. 学校", id="kanji"),
                Label("Kana Word"),
                Input(placeholder="e.g. がっこう", id="kana"),
                Label("English Word"),
                Input(placeholder="e.g. School", id="english"),
                Label("Japanese Sentence"),
                Input(placeholder="e.g. 私は毎日学校に行きます。", id="jp_sentence"),
                Label("English Sentence"),
                Input(placeholder="e.g. I go to school every day.", id="en_sentence"),
                id="form_inputs",
            ),
            Container(
                Button("Save", variant="primary", id="save_btn"),
                Button("Cancel", variant="error", id="cancel_btn"),
                id="form_buttons",
            ),
            Static("", id="status_message"),
            id="add_word_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.app.pop_screen()
        elif event.button.id == "save_btn":
            self.save_word()

    def save_word(self) -> None:
        kanji = self.query_one("#kanji", Input).value.strip()
        kana = self.query_one("#kana", Input).value.strip()
        english = self.query_one("#english", Input).value.strip()
        jp_sentence = self.query_one("#jp_sentence", Input).value.strip()
        en_sentence = self.query_one("#en_sentence", Input).value.strip()

        status = self.query_one("#status_message", Static)

        if not all([kanji, kana, english, jp_sentence, en_sentence]):
            status.update("Error: All fields are required.")
            status.add_class("error")
            return

        try:
            self.db.add_word(
                kanji=kanji,
                kana=kana,
                english=english,
                jp_sentence=jp_sentence,
                en_sentence=en_sentence,
            )
            # Clear inputs
            for input_widget in self.query(Input):
                input_widget.value = ""

            status.update("Word added successfully!")
            status.remove_class("error")
            status.add_class("success")

            # Optionally focus back to top
            self.query_one("#kanji", Input).focus()

        except Exception as e:
            status.update(f"Error saving word: {e}")
            status.add_class("error")
