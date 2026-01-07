from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static
from pydantic import ValidationError

from .db import Database
from .models import Word


class EditWordScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(self, db: Database, word_id: int):
        super().__init__()
        self.db = db
        self.word_id = word_id

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Edit Word", id="add_word_title"),
            Vertical(
                Label("Kanji Word"),
                Input(id="kanji"),
                Label("Kana Word"),
                Input(id="kana"),
                Label("English Words (each separated by ;)"),
                Input(id="english"),
                Label("Japanese Sentence"),
                Input(id="jp_sentence"),
                Label("English Sentence"),
                Input(id="en_sentence"),
                Label("Tag"),
                Input(id="tag"),
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

    def on_mount(self) -> None:
        word = self.db.get_word(self.word_id)
        if word:
            self.query_one("#kanji", Input).value = word.kanji_word
            self.query_one("#kana", Input).value = word.kana_word
            self.query_one("#english", Input).value = word.english_word
            self.query_one("#jp_sentence", Input).value = word.japanese_sentence
            self.query_one("#en_sentence", Input).value = word.english_sentence
            self.query_one("#tag", Input).value = word.tag

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self.save_word()

    def save_word(self) -> None:
        kanji = self.query_one("#kanji", Input).value.strip()
        kana = self.query_one("#kana", Input).value.strip()
        english = self.query_one("#english", Input).value.strip()
        jp_sentence = self.query_one("#jp_sentence", Input).value.strip()
        en_sentence = self.query_one("#en_sentence", Input).value.strip()
        tag = self.query_one("#tag", Input).value.strip()

        status = self.query_one("#status_message", Static)

        try:
            # Validate using Pydantic model
            word = Word(
                kanji_word=kanji,
                kana_word=kana,
                english_word=english,
                japanese_sentence=jp_sentence,
                english_sentence=en_sentence,
                tag=tag,
            )

            word.id = self.word_id
            self.db.update_word(word)
            self.dismiss(True)

        except ValidationError as e:
            # Extract first error for display
            err = e.errors()[0]
            field = str(err["loc"][0])
            msg = err["msg"]
            status.update(f"Error: {field} {msg}")
            status.add_class("error")

        except Exception as e:
            status.update(f"Error updating word: {e}")
            status.add_class("error")
