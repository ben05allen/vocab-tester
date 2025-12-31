import pytest
from unittest.mock import MagicMock
from vocab_tester.quiz_screen import QuizScreen
from vocab_tester.models import Word


# Mock Database
class MockDatabase:
    def get_random_word(self, tag_filter=None):
        return Word(
            id=1,
            kanji_word="Kanji",
            japanese_sentence="Sentence",
            kana_word="Kana",
            english_word="Meaning",
            english_sentence="EngSentence",
            tag="Tag",
        )

    def record_result(self, word_id, correct):
        pass


# Testable subclass to mock UI elements
class MockQuizScreen(QuizScreen):
    def __init__(self, db):
        super().__init__(db)
        self._mocks = {}

    def query_one(self, selector, type=None):
        if selector not in self._mocks:
            m = MagicMock()
            m.value = ""
            m.styles = MagicMock()
            self._mocks[selector] = m
        return self._mocks[selector]

    @property
    def app(self):
        return MagicMock()


@pytest.fixture
def screen():
    db = MockDatabase()
    return MockQuizScreen(db)


def test_queue_initialization(screen):
    """Test that queue is populated on mount/next_question."""
    screen.next_question()
    # Logic: fills to 10, pops 1 -> 9 left
    assert len(screen.queue) == 9
    assert isinstance(screen.question_data, Word)
    assert screen.question_data.kanji_word == "Kanji"


def test_incorrect_answer_requeues(screen):
    """Test that incorrect answers are re-inserted into the queue."""
    screen.next_question()
    initial_word = screen.question_data

    # Input incorrect answers
    screen.kana_answer = "Wrong"
    screen.meaning_answer = "Wrong"

    # Initial queue size should be 9
    assert len(screen.queue) == 9

    # Trigger results
    screen.show_results()

    # Queue should now have the word inserted at 2 and 5
    # Size 9 + 2 = 11
    assert len(screen.queue) == 11

    assert screen.queue[2] == initial_word
    assert screen.queue[5] == initial_word


def test_correct_answer_does_not_requeue(screen):
    """Test that correct answers are NOT re-inserted."""
    screen.next_question()

    screen.kana_answer = "Kana"
    screen.meaning_answer = "Meaning"  # Case insensitive check in code

    screen.show_results()

    # Queue size should remain 9 (or technically, it might not change,
    # but specifically it shouldn't grow by 2)
    # Actually, next_question pops one, so we are at 9.
    assert len(screen.queue) == 9
    # Show results just records. It doesn't pop new one yet.
    assert len(screen.queue) == 9


def test_filter_tag_updates_queue(screen):
    """Test that applying a filter clears queue and requests filtered words."""
    screen.on_filter_selected("SomeTag")

    assert screen.current_tag_filter == "SomeTag"
    # Queue should be cleared and refilled.
    # MockDatabase.get_random_word signature needs update in this file first probably.
    assert len(screen.queue) == 9  # It refills to 10 then pops 1
    screen.query_one("#filter_label").update.assert_called_with("Filter: SomeTag")


def test_filter_clear(screen):
    screen.current_tag_filter = "OldTag"
    screen.on_filter_selected("")  # Clear

    assert screen.current_tag_filter is None
    screen.query_one("#filter_label").update.assert_called_with("Filter: All")
