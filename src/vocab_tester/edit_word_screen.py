from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from .db import Database


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
                Label("English Word"),
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
            # word schema: id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag
            _, kanji, jp_sentence, kana, english, en_sentence, tag = word

            self.query_one("#kanji", Input).value = kanji
            self.query_one("#kana", Input).value = kana
            self.query_one("#english", Input).value = english
            self.query_one("#jp_sentence", Input).value = jp_sentence
            self.query_one("#en_sentence", Input).value = en_sentence
            self.query_one("#tag", Input).value = tag

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

        if not all([kanji, kana, english, jp_sentence, en_sentence, tag]):
            status.update("Error: All fields are required.")
            status.add_class("error")
            return

        try:
            self.db.update_word(
                word_id=self.word_id,
                kanji=kanji,
                kana=kana,
                english=english,
                jp_sentence=jp_sentence,
                en_sentence=en_sentence,
                tag=tag,
            )
            self.dismiss(True)

        except Exception as e:
            status.update(f"Error updating word: {e}")
            status.add_class("error")
