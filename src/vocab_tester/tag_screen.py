from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from .db import Database


class TagSelectionScreen(ModalScreen[str | None]):
    CSS_PATH = "styles.tcss"

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Select Tag to Filter", id="tag_select_title"),
            VerticalScroll(
                Button("All Words (No Filter)", id="filter_all", variant="primary"),
                id="tag_list",
            ),
            Button("Cancel", variant="error", id="cancel_btn"),
            id="tag_selection_container",
        )

    def on_mount(self) -> None:
        tag_list = self.query_one("#tag_list", VerticalScroll)
        tags = self.db.get_tags()

        for tag in tags:
            # Create a button for each tag.
            # We use the tag name as the label.
            # We can't use the tag as ID directly if it has spaces or invalid chars,
            # but for simple implementation we can use a custom attribute or just check label in handler.
            # Using a class for tag buttons helps identifying them.
            btn = Button(tag, classes="tag-button")
            # We can store the tag value on the button itself if we subclass or just use the label
            tag_list.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(None)  # No change / Cancel
        elif event.button.id == "filter_all":
            self.dismiss("")  # Empty string = All/No filter
        elif "tag-button" in event.button.classes:
            # The label of the button is the tag
            self.dismiss(str(event.button.label))
