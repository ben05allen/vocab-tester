import pytest
from vocab_tester.db import Database
from vocab_tester.models import Word


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_vocab_edit.db"
    db = Database(db_path=db_file)
    return db


def test_get_and_update_word(temp_db):
    # Add a word first
    old_word = Word(
        kanji_word="OldKanji",
        kana_word="OldKana",
        english_word="OldEng",
        japanese_sentence="OldJP",
        english_sentence="OldEN",
        tag="OldTag",
    )
    temp_db.add_word(old_word)

    # Get it to find ID
    con = temp_db.get_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM words WHERE kanji_word='OldKanji'")
    word_id = cur.fetchone()[0]
    con.close()

    # Test get_word
    word = temp_db.get_word(word_id)
    assert word is not None
    assert word.kanji_word == "OldKanji"

    # Test update_word
    new_word = Word(
        id=word_id,
        kanji_word="NewKanji",
        kana_word="NewKana",
        english_word="NewEng",
        japanese_sentence="NewJP",
        english_sentence="NewEN",
        tag="NewTag",
    )
    temp_db.update_word(new_word)

    updated_word = temp_db.get_word(word_id)
    assert updated_word.kanji_word == "NewKanji"
    assert updated_word.kana_word == "NewKana"
    assert updated_word.english_word == "NewEng"
    assert updated_word.japanese_sentence == "NewJP"
    assert updated_word.english_sentence == "NewEN"
    assert updated_word.tag == "NewTag"
