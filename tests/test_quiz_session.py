from unittest.mock import MagicMock

from vocab_tester.models import Word
from vocab_tester.quiz_session import QuizSession


class MockDatabase:
    def get_word(self, word_id):
        return Word(
            id=word_id,
            kanji_word=f"Word{word_id}",
            japanese_sentence="Sentence",
            kana_word="Kana",
            english_word="Meaning",
            english_sentence="EngSentence",
            tag="Tag",
        )

    def get_incorrect_word_ids(self, limit, tag_filter=None, exclude_ids=None):
        return [2, 3]

    def get_random_word_ids(self, limit, tag_filter=None, exclude_ids=None):
        return [4, 5, 6]

    def record_result(self, word_id, correct):
        pass


def test_quiz_session_initialization():
    db = MockDatabase()
    session = QuizSession(db, "MyTag")
    assert session.current_tag_filter == "MyTag"
    assert len(session.queue) == 0
    assert session.current_word is None


def test_quiz_session_next_question():
    db = MockDatabase()
    session = QuizSession(db)

    # next_question should fetch incorrect words first, then random, and return current word
    word = session.next_question()
    assert word is not None
    assert word.id == 2
    assert session.current_word == word
    assert len(session.queue) > 0


def test_quiz_session_record_result_correct():
    db = MockDatabase()
    db.record_result = MagicMock()
    session = QuizSession(db)
    session.next_question()  # sets current_word to id 2

    session.record_result(True)
    db.record_result.assert_called_with(2, True)


def test_quiz_session_record_result_incorrect():
    db = MockDatabase()
    db.record_result = MagicMock()
    session = QuizSession(db)
    session.next_question()  # current_word = id 2

    # For incorrect answers, it should re-queue the current word id 2 at indices 2 and 5
    session.record_result(False)
    db.record_result.assert_called_with(2, False)
    assert session.queue[2] == 2
    assert session.queue[5] == 2


def test_quiz_session_test_again():
    db = MockDatabase()
    session = QuizSession(db)
    session.next_question()  # current_word = id 2

    session.test_again()
    # Next question after test_again should be id 2 because it was prepended to the queue
    assert session.current_word.id == 2
