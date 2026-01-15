import pytest
from vocab_tester.db import Database
from vocab_tester.models import Word


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
    assert hasattr(word, "kanji_word")


def test_record_result(temp_db):
    """Test recording a result."""
    # First ensure we have a word
    word = temp_db.get_random_word()
    word_id = word.id

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
    word = Word(
        kanji_word="テスト",
        kana_word="てすと",
        english_word="test",
        japanese_sentence="これはテストです。",
        english_sentence="This is a test.",
        tag="noun",
    )

    temp_db.add_word(word)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM words WHERE kanji_word = ?",
        (word.kanji_word,),
    )
    row = cur.fetchone()
    con.close()

    assert row is not None
    # schema: id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag
    assert row[1] == word.kanji_word
    assert row[2] == word.japanese_sentence
    assert row[3] == word.kana_word
    assert row[4] == word.english_word
    assert row[5] == word.english_sentence
    assert row[6] == word.tag


def test_add_word_tag_fallback(temp_db):
    """Test that tag falls back to 'none' if empty."""
    word = Word(
        kanji_word="Fallback",
        kana_word="fallback",
        english_word="fallback",
        japanese_sentence="fallback",
        english_sentence="fallback",
        tag="none",
    )

    temp_db.add_word(word)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT tag FROM words WHERE kanji_word = ?", (word.kanji_word,))
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
    temp_db.add_word(
        Word(
            kanji_word="W1",
            kana_word="w1",
            english_word="w1",
            japanese_sentence="s1",
            english_sentence="s1",
            tag="TagA",
        )
    )
    # Word 2: Tag B
    temp_db.add_word(
        Word(
            kanji_word="W2",
            kana_word="w2",
            english_word="w2",
            japanese_sentence="s2",
            english_sentence="s2",
            tag="TagB",
        )
    )
    # Word 3: Tag A again
    temp_db.add_word(
        Word(
            kanji_word="W3",
            kana_word="w3",
            english_word="w3",
            japanese_sentence="s3",
            english_sentence="s3",
            tag="TagA",
        )
    )

    # TagA max ID is associated with the latest entry.
    # Order should be TagA, TagB because TagA was used last.

    tags = temp_db.get_tags()
    assert tags == ["TagA", "TagB"]

    # Add Word 4: Tag C
    temp_db.add_word(
        Word(
            kanji_word="W4",
            kana_word="w4",
            english_word="w4",
            japanese_sentence="s4",
            english_sentence="s4",
            tag="TagC",
        )
    )
    # Order should be TagC (4), TagA (3), TagB (2)
    tags = temp_db.get_tags()
    assert tags == ["TagC", "TagA", "TagB"]

    # Add Word 5: Tag B again
    temp_db.add_word(
        Word(
            kanji_word="W5",
            kana_word="w5",
            english_word="w5",
            japanese_sentence="s5",
            english_sentence="s5",
            tag="TagB",
        )
    )
    # Order should be TagB (5), TagC (4), TagA (3)
    tags = temp_db.get_tags()
    assert tags == ["TagB", "TagC", "TagA"]


def test_get_random_word_filtered(temp_db):
    """Test filtering random words by tag."""
    temp_db.add_word(
        Word(
            kanji_word="WA",
            kana_word="wa",
            english_word="wa",
            japanese_sentence="sa",
            english_sentence="sa",
            tag="TagA",
        )
    )
    temp_db.add_word(
        Word(
            kanji_word="WB",
            kana_word="wb",
            english_word="wb",
            japanese_sentence="sb",
            english_sentence="sb",
            tag="TagB",
        )
    )

    # Filter for TagA
    word = temp_db.get_random_word(tag_filter="TagA")
    assert word is not None
    assert word.tag == "TagA"

    # Filter for TagB
    word = temp_db.get_random_word(tag_filter="TagB")
    assert word is not None
    assert word.tag == "TagB"

    # Filter for non-existent tag
    word = temp_db.get_random_word(tag_filter="NonExistent")
    assert word is None


def test_get_incorrect_words(temp_db):
    """Test fetching incorrect words."""
    # 1. Create a word and record it as incorrect
    word = Word(
        kanji_word="Incorrect",
        kana_word="incorrect",
        english_word="incorrect",
        japanese_sentence="inc",
        english_sentence="inc",
        tag="inc_tag",
    )
    temp_db.add_word(word)

    # We need the ID. Since add_word doesn't return ID, we fetch it.
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word = 'Incorrect'")
    w_id = cur.fetchone()[0]
    con.close()

    temp_db.record_result(w_id, correct=False)

    # 2. Fetch incorrect words
    words = temp_db.get_incorrect_words(limit=10)
    assert len(words) >= 1
    found = False
    for w in words:
        if w.kanji_word == "Incorrect":
            found = True
            break
    assert found

    # 3. Test filter
    words = temp_db.get_incorrect_words(limit=10, tag_filter="OtherTag")
    # Should not find it
    found = False
    for w in words:
        if w.kanji_word == "Incorrect":
            found = True
    assert not found

    # 4. Test excludes
    words = temp_db.get_incorrect_words(limit=10, exclude_ids=[w_id])
    found = False
    for w in words:
        if w.kanji_word == "Incorrect":
            found = True
    assert not found


def test_get_incorrect_word_ids(temp_db):
    """Test fetching incorrect word IDs."""
    # 1. Create a word and record it as incorrect
    word = Word(
        kanji_word="IncorrectID",
        kana_word="incorrect",
        english_word="incorrect",
        japanese_sentence="inc",
        english_sentence="inc",
        tag="inc_tag",
    )
    temp_db.add_word(word)

    # We need the ID.
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word = 'IncorrectID'")
    w_id = cur.fetchone()[0]
    con.close()

    temp_db.record_result(w_id, correct=False)

    # 2. Fetch incorrect word IDs
    ids = temp_db.get_incorrect_word_ids(limit=10)
    assert len(ids) >= 1
    assert w_id in ids

    # 3. Test filter
    ids = temp_db.get_incorrect_word_ids(limit=10, tag_filter="OtherTag")
    assert w_id not in ids

    # 4. Test excludes
    ids = temp_db.get_incorrect_word_ids(limit=10, exclude_ids=[w_id])
    assert w_id not in ids


def test_get_random_words_excludes(temp_db):
    """Test get_random_words respects exclusions."""
    word = Word(
        kanji_word="ExcludeMe",
        kana_word="x",
        english_word="x",
        japanese_sentence="x",
        english_sentence="x",
        tag="x",
    )
    temp_db.add_word(word)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word = 'ExcludeMe'")
    w_id = cur.fetchone()[0]
    con.close()

    # Exclude it
    words = temp_db.get_random_words(limit=100, exclude_ids=[w_id])
    for w in words:
        assert w.kanji_word != "ExcludeMe"


def test_get_random_word_ids_excludes(temp_db):
    """Test get_random_word_ids respects exclusions."""
    word = Word(
        kanji_word="ExcludeMeID",
        kana_word="x",
        english_word="x",
        japanese_sentence="x",
        english_sentence="x",
        tag="x",
    )
    temp_db.add_word(word)

    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word = 'ExcludeMeID'")
    w_id = cur.fetchone()[0]
    con.close()

    # Exclude it
    ids = temp_db.get_random_word_ids(limit=100, exclude_ids=[w_id])
    assert w_id not in ids
