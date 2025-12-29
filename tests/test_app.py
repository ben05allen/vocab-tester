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


@pytest.mark.asyncio
async def test_score_logic():
    app = VocabTesterApp()

    # Simulate on_mount initialization
    app.on_mount()

    assert app.score_correct == 0
    assert app.score_total == 0
    assert "Score: 0/0" in app.sub_title

    app.update_score(is_correct=True)
    assert app.score_correct == 1
    assert app.score_total == 1
    assert "Score: 1/1" in app.sub_title

    app.update_score(is_correct=False)
    assert app.score_correct == 1
    assert app.score_total == 2
    assert "Score: 1/2" in app.sub_title
