import pytest
from unittest.mock import MagicMock
from vocab_tester.quiz_screen import QuizScreen


class MockDatabase:
    def get_word(self, word_id):
        if word_id == 1:
            return (1, "NewKanji", "NewJP", "NewKana", "NewEng", "NewEN", "NewTag")
        return None

    def get_random_word(self):
        return (1, "OldKanji", "OldJP", "OldKana", "OldEng", "OldEN", "OldTag")

    def record_result(self, *args):
        pass


class MockQuizScreen(QuizScreen):
    def __init__(self, db):
        super().__init__(db)
        self._mocks = {}
        self.app_mock = MagicMock()

    def query_one(self, selector, type=None):
        if selector not in self._mocks:
            m = MagicMock()
            m.value = ""
            self._mocks[selector] = m
        return self._mocks[selector]

    @property
    def app(self):
        return self.app_mock


@pytest.fixture
def screen():
    db = MockDatabase()
    return MockQuizScreen(db)


def test_action_edit_word_pushes_screen(screen):
    screen.step = "result"
    screen.question_data = (1, "Kanji", "JP", "Kana", "Eng", "EnSent", "Tag")

    screen.action_edit_word()

    screen.app.push_screen.assert_called()
    call_args = screen.app.push_screen.call_args
    # First arg is screen instance, second is callback
    assert call_args[0][1] == screen.on_edit_word_done


def test_on_edit_word_done_refreshes_data(screen):
    screen.question_data = (
        1,
        "OldKanji",
        "OldJP",
        "OldKana",
        "OldEng",
        "OldEN",
        "OldTag",
    )
    # Simulate editing done with changes
    screen.on_edit_word_done(True)

    # Check if data updated
    assert screen.question_data == (
        1,
        "NewKanji",
        "NewJP",
        "NewKana",
        "NewEng",
        "NewEN",
        "NewTag",
    )
    assert screen.kanji == "NewKanji"

    # Check if UI updated
    screen.query_one("#full_info").update.assert_called()
    screen.query_one("#sentence_label").update.assert_called_with("NewJP")
