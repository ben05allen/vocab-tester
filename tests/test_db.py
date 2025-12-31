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
    assert len(word) == 7  # (id, kanji, sentence, kana, meaning, eng_sentence, tag)


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


def test_add_word(temp_db):
    """Test adding a new word."""
    kanji = "テスト"
    kana = "てすと"
    english = "test"
    jp_sentence = "これはテストです。"
    en_sentence = "This is a test."
    tag = "noun"

    temp_db.add_word(kanji, kana, english, jp_sentence, en_sentence, tag)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM words WHERE kanji_word = ?",
        (kanji,),
    )
    row = cur.fetchone()
    con.close()

    assert row is not None
    # schema: id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag
    assert row[1] == kanji
    assert row[2] == jp_sentence
    assert row[3] == kana
    assert row[4] == english
    assert row[5] == en_sentence
    assert row[6] == tag


def test_add_word_tag_fallback(temp_db):
    """Test that tag falls back to 'none' if empty."""
    kanji = "Fallback"
    kana = "fallback"
    english = "fallback"
    jp_sentence = "fallback"
    en_sentence = "fallback"

    # Pass empty string for tag
    temp_db.add_word(kanji, kana, english, jp_sentence, en_sentence, tag="")

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT tag FROM words WHERE kanji_word = ?", (kanji,))
    tag = cur.fetchone()[0]
    con.close()

    assert tag == "none"


def test_get_tags_ordering(temp_db):
    """Test that tags are returned ordered by most recent word ID."""
    # Clear seeded data
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM words")
    con.commit()
    con.close()

    # Add words with different tags
    # Word 1: Tag A
    temp_db.add_word("W1", "w1", "w1", "s1", "s1", "TagA")
    # Word 2: Tag B
    temp_db.add_word("W2", "w2", "w2", "s2", "s2", "TagB")
    # Word 3: Tag A again
    temp_db.add_word("W3", "w3", "w3", "s3", "s3", "TagA")

    # TagA max ID is associated with the latest entry.
    # Order should be TagA, TagB because TagA was used last.

    tags = temp_db.get_tags()
    assert tags == ["TagA", "TagB"]

    # Add Word 4: Tag C
    temp_db.add_word("W4", "w4", "w4", "s4", "s4", "TagC")
    # Order should be TagC (4), TagA (3), TagB (2)
    tags = temp_db.get_tags()
    assert tags == ["TagC", "TagA", "TagB"]

    # Add Word 5: Tag B again
    temp_db.add_word("W5", "w5", "w5", "s5", "s5", "TagB")
    # Order should be TagB (5), TagC (4), TagA (3)
    tags = temp_db.get_tags()
    assert tags == ["TagB", "TagC", "TagA"]


def test_get_random_word_filtered(temp_db):
    """Test filtering random words by tag."""
    temp_db.add_word("WA", "wa", "wa", "sa", "sa", "TagA")
    temp_db.add_word("WB", "wb", "wb", "sb", "sb", "TagB")

    # Filter for TagA
    word = temp_db.get_random_word(tag_filter="TagA")
    assert word is not None
    assert word[6] == "TagA"

    # Filter for TagB
    word = temp_db.get_random_word(tag_filter="TagB")
    assert word is not None
    assert word[6] == "TagB"

    # Filter for non-existent tag
    word = temp_db.get_random_word(tag_filter="NonExistent")
    assert word is None
