import pytest
from unittest.mock import MagicMock
from vocab_tester.quiz_screen import QuizScreen


# Mock Database
class MockDatabase:
    def get_random_word(self):
        # return (id, kanji, sentence, kana, meaning, eng_sentence, tag)
        return (1, "Kanji", "Sentence", "Kana", "Meaning", "EngSentence", "Tag")

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
    assert screen.question_data == (
        1,
        "Kanji",
        "Sentence",
        "Kana",
        "Meaning",
        "EngSentence",
        "Tag",
    )


def test_incorrect_answer_requeues(screen):
    """Test that incorrect answers are re-inserted into the queue."""
    screen.next_question()
    initial_word = screen.question_data

    # Simulate setup
    screen.kana = "Kana"
    screen.meaning = "Meaning"

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

    screen.kana = "Kana"
    screen.meaning = "Meaning"

    screen.kana_answer = "Kana"
    screen.meaning_answer = "Meaning"  # Case insensitive check in code

    screen.show_results()

    # Queue size should remain 9 (or technically, it might not change,
    # but specifically it shouldn't grow by 2)
    # Actually, next_question pops one, so we are at 9.
    # Show results just records. It doesn't pop new one yet.
    assert len(screen.queue) == 9
