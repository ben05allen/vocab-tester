import pytest
import asyncio
from unittest.mock import MagicMock
from textual.app import App
from vocab_tester.add_word_screen import AddWordScreen
from vocab_tester.ai_service import GeneratedWordData


class MockDatabase:
    def add_word(self, word):
        pass


class AddWordApp(App):
    def on_mount(self) -> None:
        self.push_screen(AddWordScreen(MockDatabase()))


@pytest.mark.asyncio
async def test_generate_ai_data_updates_inputs():
    mock_data = GeneratedWordData(
        kana_word="がっこう",
        english_word="school",
        japanese_sentence="学校に行きます。",
        english_sentence="I go to school.",
    )

    app = AddWordApp()
    async with app.run_test() as pilot:
        # Mock the AI service
        screen = app.screen
        # Wait for the screen to be the expected one
        for _ in range(100):
            if isinstance(screen, AddWordScreen):
                break
            await asyncio.sleep(0.01)
            screen = app.screen

        assert isinstance(screen, AddWordScreen)
        screen.ai_service = MagicMock()
        screen.ai_service.generate_word_data.return_value = mock_data

        # Set kanji input directly
        screen.query_one("#kanji").value = "学校"

        # Click generate
        await pilot.click("#generate_btn")

        # Wait for the worker to finish
        for _ in range(20):
            if screen.query_one("#kana").value == "がっこう":
                break
            await asyncio.sleep(0.1)

        # Check if values are populated
        assert screen.query_one("#kana").value == "がっこう"
        assert screen.query_one("#english").value == "school"
        assert screen.query_one("#jp_sentence").value == "学校に行きます。"
        assert screen.query_one("#en_sentence").value == "I go to school."
