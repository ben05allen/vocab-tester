import pytest
from vocab_tester.db import Database


@pytest.fixture
def temp_db(tmp_path):
    """Fixture to create a temporary database."""
    db_file = tmp_path / "test_vocab.db"
    db = Database(db_path=db_file)
    return db


def test_init_creates_tables(temp_db):
    """Test that initializing the database creates the necessary tables."""
    con = temp_db.get_connection()
    cur = con.cursor()

    # Check words table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    assert cur.fetchone() is not None

    # Check last_tested table
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='last_tested'"
    )
    # Note: currently the schema file has last_tested, but let's double check if my read of db.py earlier initialized it.
    # Looking at db.py _init_db method, it executes the whole script.
    assert cur.fetchone() is not None

    con.close()


def test_seed_data(temp_db):
    """Test that the database is seeded with initial data."""
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM words")
    count = cur.fetchone()[0]
    assert count > 0
    con.close()


def test_get_random_word(temp_db):
    """Test fetching a random word."""
    word = temp_db.get_random_word()
    assert word is not None
    assert len(word) == 6  # (id, kanji, sentence, kana, meaning, eng_sentence)


def test_record_result(temp_db):
    """Test recording a result."""
    # First ensure we have a word
    word = temp_db.get_random_word()
    word_id = word[0]

    # Record a correct answer
    temp_db.record_result(word_id, True)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT last_correct FROM last_tested WHERE word_id = ?", (word_id,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == 1

    # Update to incorrect
    temp_db.record_result(word_id, False)
    cur.execute("SELECT last_correct FROM last_tested WHERE word_id = ?", (word_id,))
    row = cur.fetchone()
    assert row[0] == 0

    con.close()
