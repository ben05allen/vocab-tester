import pytest
from unittest.mock import MagicMock
from vocab_tester.quiz_screen import QuizScreen
from vocab_tester.models import Word


class MockDatabase:
    def get_word(self, word_id):
        if word_id == 1:
            return Word(
                id=1,
                kanji_word="NewKanji",
                japanese_sentence="NewJP",
                kana_word="NewKana",
                english_word="NewEng",
                english_sentence="NewEN",
                tag="NewTag",
            )
        return None

    def get_random_word(self, tag_filter=None):
        return Word(
            id=1,
            kanji_word="OldKanji",
            japanese_sentence="OldJP",
            kana_word="OldKana",
            english_word="OldEng",
            english_sentence="OldEN",
            tag="OldTag",
        )

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
    screen.question_data = Word(
        id=1,
        kanji_word="Kanji",
        japanese_sentence="JP",
        kana_word="Kana",
        english_word="Eng",
        english_sentence="EnSent",
        tag="Tag",
    )

    screen.action_edit_word()

    screen.app.push_screen.assert_called()
    call_args = screen.app.push_screen.call_args
    # First arg is screen instance, second is callback
    assert call_args[0][1] == screen.on_edit_word_done


def test_on_edit_word_done_refreshes_data(screen):
    screen.question_data = Word(
        id=1,
        kanji_word="OldKanji",
        japanese_sentence="OldJP",
        kana_word="OldKana",
        english_word="OldEng",
        english_sentence="OldEN",
        tag="OldTag",
    )
    # Simulate editing done with changes
    screen.on_edit_word_done(True)

    # Check if data updated
    assert screen.question_data.kanji_word == "NewKanji"

    # Check if UI updated
    screen.query_one("#full_info").update.assert_called()
    screen.query_one("#sentence_label").update.assert_called_with("NewJP")
