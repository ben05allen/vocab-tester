from unittest.mock import MagicMock, patch
from vocab_tester.quiz_screen import QuizScreen


# Re-using MockQuizScreen logic or similar
class MockQuizScreen(QuizScreen):
    def __init__(self, db):
        super().__init__(db)
        self._mocks = {}
        self.app_mock = MagicMock()

    def query_one(self, selector, type=None):
        if selector not in self._mocks:
            m = MagicMock()
            m.value = ""
            m.styles = MagicMock()
            self._mocks[selector] = m
        return self._mocks[selector]

    @property
    def app(self):
        return self.app_mock


def test_default_filter_applied_on_mount():
    mock_db = MagicMock()
    mock_db.get_tags.return_value = ["spring26", "other"]
    # Mock next_question to avoid queue filling logic in this test
    with patch.object(QuizScreen, "next_question"):
        with patch("vocab_tester.quiz_screen.config", {"default-filter": "spring26"}):
            screen = MockQuizScreen(mock_db)
            screen.on_mount()

            assert screen.current_tag_filter == "spring26"
            screen.query_one("#filter_label").update.assert_called_with(
                "Filter: spring26"
            )


def test_default_filter_ignored_if_invalid():
    mock_db = MagicMock()
    mock_db.get_tags.return_value = ["other"]
    with patch.object(QuizScreen, "next_question"):
        with patch("vocab_tester.quiz_screen.config", {"default-filter": "spring26"}):
            screen = MockQuizScreen(mock_db)
            screen.on_mount()

            assert screen.current_tag_filter is None
            # Check that it wasn't called with the invalid filter
            for call in screen.query_one("#filter_label").update.call_args_list:
                assert "spring26" not in call[0][0]


def test_no_default_filter():
    mock_db = MagicMock()
    mock_db.get_tags.return_value = ["spring26", "other"]
    with patch.object(QuizScreen, "next_question"):
        with patch("vocab_tester.quiz_screen.config", {}):
            screen = MockQuizScreen(mock_db)
            screen.on_mount()

            assert screen.current_tag_filter is None
