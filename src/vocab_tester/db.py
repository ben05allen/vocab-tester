import sqlite3
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = Path("data/vocab.db")
SCHEMA_PATH = Path("ref/sqlite3-schema.txt")


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initialize the database with schema if tables don't exist."""
        # Ensure schema file exists, if not, we can't init, but assuming it exists per check
        if not SCHEMA_PATH.exists():
            # Fallback or error, but for this env we assume it's there
            pass

        con = self.get_connection()
        cur = con.cursor()

        # Check if table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='words'"
        )
        if not cur.fetchone():
            with open(SCHEMA_PATH, "r") as f:
                schema = f.read()
            cur.executescript(schema)
            self._seed_data(con)

        con.close()

    def _seed_data(self, con: sqlite3.Connection) -> None:
        """Add sample data for testing."""
        samples = [
            (
                "学校",
                "私は毎日学校に行きます。",
                "がっこう",
                "school",
                "I go to school every day.",
            ),
            (
                "猫",
                "猫がベッドで寝ています。",
                "ねこ",
                "cat",
                "The cat is sleeping on the bed.",
            ),
            ("食べる", "朝ご飯を食べる。", "たべる", "eat", "I eat breakfast."),
            (
                "勉強",
                "日本語を勉強しています。",
                "べんきょう",
                "study",
                "I am studying Japanese.",
            ),
        ]
        cur = con.cursor()
        cur.executemany(
            "INSERT INTO words (kanji_word, japanese_sentence, kana_word, english_word, english_sentence) VALUES (?, ?, ?, ?, ?)",
            samples,
        )
        con.commit()

    def get_random_word(self) -> Optional[Tuple[int, str, str, str, str, str]]:
        """
        Returns a random word tuple:
        (id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence)
        """
        con = self.get_connection()
        cur = con.cursor()
        # Simple random selection for now
        cur.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        con.close()
        return row

    def record_result(self, word_id: int, correct: bool) -> None:
        """Records the result of a test."""
        # This is a placeholder for future logic (e.g. spaced repetition)
        con = self.get_connection()
        cur = con.cursor()
        # Check if exists
        cur.execute("SELECT id FROM last_tested WHERE word_id = ?", (word_id,))
        row = cur.fetchone()
        import time

        timestamp = int(time.time())

        if row:
            cur.execute(
                "UPDATE last_tested SET last_seen = ?, last_correct = ? WHERE word_id = ?",
                (timestamp, 1 if correct else 0, word_id),
            )
        else:
            cur.execute(
                "INSERT INTO last_tested (word_id, last_seen, last_correct) VALUES (?, ?, ?)",
                (word_id, timestamp, 1 if correct else 0),
            )
        con.commit()
        con.close()
