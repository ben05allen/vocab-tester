import pytest
from vocab_tester.db import Database


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_vocab_edit.db"
    db = Database(db_path=db_file)
    return db


def test_get_and_update_word(temp_db):
    # Add a word first
    temp_db.add_word("OldKanji", "OldKana", "OldEng", "OldJP", "OldEN", "OldTag")

    # Get it to find ID
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word='OldKanji'")
    word_id = cur.fetchone()[0]
    con.close()

    # Test get_word
    word = temp_db.get_word(word_id)
    assert word is not None
    assert word[1] == "OldKanji"

    # Test update_word
    temp_db.update_word(
        word_id, "NewKanji", "NewKana", "NewEng", "NewJP", "NewEN", "NewTag"
    )

    updated_word = temp_db.get_word(word_id)
    assert updated_word[1] == "NewKanji"
    assert updated_word[3] == "NewKana"
    assert updated_word[4] == "NewEng"
    assert updated_word[2] == "NewJP"
    assert updated_word[5] == "NewEN"
    assert updated_word[6] == "NewTag"
