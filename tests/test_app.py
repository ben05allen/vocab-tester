import pytest
from vocab_tester.app import VocabTesterApp


@pytest.mark.asyncio
async def test_toggle_dark():
    app = VocabTesterApp()
    # Initial state (default is usually dark or system dependent, but let's check what it is and toggle)
    initial_theme = app.theme

    # Run the action
    app.action_toggle_dark()

    # Assert it changed
    assert app.theme != initial_theme

    # Toggle back
    app.action_toggle_dark()
    assert app.theme == initial_theme
