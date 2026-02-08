import pytest
import asyncio
from unittest.mock import MagicMock
from textual.app import App
from vocab_tester.edit_word_screen import EditWordScreen
from vocab_tester.models import Word
from vocab_tester.ai_service import GeneratedWordData


class MockDatabase:
    def get_word(self, word_id: int):
        return Word(
            id=word_id,
            kanji_word="学校",
            kana_word="がっこう",
            english_word="School",
            japanese_sentence="私は毎日学校に行きます。",
            english_sentence="I go to school every day.",
            tag="noun",
        )

    def update_word(self, word: Word):
        pass


class EditWordApp(App):
    def on_mount(self) -> None:
        self.push_screen(EditWordScreen(MockDatabase(), 1))


@pytest.mark.asyncio
async def test_edit_screen_generate_ai_data_updates_inputs():
    """Test that the generate button updates inputs in the EditWordScreen."""
    mock_data = GeneratedWordData(
        kana_word="あたらしい",
        english_word="new",
        japanese_sentence="これは新しい本です。",
        english_sentence="This is a new book.",
    )

    app = EditWordApp()
    async with app.run_test() as pilot:
        screen = app.screen
        # Wait for the screen to be the expected one
        for _ in range(100):
            if isinstance(screen, EditWordScreen):
                break
            await asyncio.sleep(0.01)
            screen = app.screen

        assert isinstance(screen, EditWordScreen)

        # Verify initial values are loaded
        assert screen.query_one("#kanji").value == "学校"
        assert screen.query_one("#kana").value == "がっこう"

        # Mock the AI service
        screen.ai_service = MagicMock()
        screen.ai_service.generate_word_data.return_value = mock_data

        # Change kanji input
        screen.query_one("#kanji").value = "新しい"

        # Click generate
        await pilot.click("#generate_btn")

        # Wait for the worker to finish and update UI
        # We loop and check because the worker runs in background
        success = False
        for _ in range(20):
            if screen.query_one("#kana").value == "あたらしい":
                success = True
                break
            await asyncio.sleep(0.1)

        assert success, "UI did not update with generated data"

        # Check if values are populated
        assert screen.query_one("#kana").value == "あたらしい"
        assert screen.query_one("#english").value == "new"
        assert screen.query_one("#jp_sentence").value == "これは新しい本です。"
        assert screen.query_one("#en_sentence").value == "This is a new book."
