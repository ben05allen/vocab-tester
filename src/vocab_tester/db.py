import sqlite3
import time
from pathlib import Path

from .models import Word
from .seeds import SAMPLES

DB_PATH = Path("data/vocab.db")
SCHEMA_PATH = Path("ref/sqlite3-schema.txt")


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

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
        cur = con.cursor()
        cur.executemany(
            "INSERT INTO words (kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag) VALUES (?, ?, ?, ?, ?, ?)",
            SAMPLES,
        )
        con.commit()

    def get_random_word(self, tag_filter: str | None = None) -> Word | None:
        """
        Returns a random word object.
        """
        con = self.get_connection()
        cur = con.cursor()

        if tag_filter:
            cur.execute(
                "SELECT * FROM words WHERE tag = ? ORDER BY RANDOM() LIMIT 1",
                (tag_filter,),
            )
        else:
            cur.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")

        row = cur.fetchone()
        con.close()

        if row:
            return Word(**dict(row))
        return None

    def get_random_words(
        self,
        limit: int,
        tag_filter: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[Word]:
        """
        Returns a list of random word objects.
        """
        con = self.get_connection()
        cur = con.cursor()

        query = "SELECT * FROM words WHERE 1=1"
        params = []

        if tag_filter:
            query += " AND tag = ?"
            params.append(tag_filter)

        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        con.close()

        return [Word(**dict(row)) for row in rows]

    def get_incorrect_words(
        self,
        limit: int,
        tag_filter: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[Word]:
        """
        Returns a list of words that were last answered incorrectly.
        """
        con = self.get_connection()
        cur = con.cursor()

        query = """
            SELECT w.*
            FROM words w
            JOIN last_tested lt ON w.id = lt.word_id
            WHERE lt.last_correct = 0
        """
        params = []

        if tag_filter:
            query += " AND w.tag = ?"
            params.append(tag_filter)

        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            query += f" AND w.id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        con.close()

        return [Word(**dict(row)) for row in rows]

    def get_tags(self) -> list[str]:
        """
        Returns a list of all unique tags, ordered by the ID of the most recent word using that tag.
        """
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(
            "SELECT tag, MAX(id) as max_id FROM words GROUP BY tag ORDER BY max_id DESC"
        )
        rows = cur.fetchall()
        con.close()
        return [row["tag"] for row in rows]

    def get_word(self, word_id: int) -> Word | None:
        """
        Returns a word object by ID.
        """
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM words WHERE id = ?", (word_id,))
        row = cur.fetchone()
        con.close()

        if row:
            return Word(**dict(row))
        return None

    def update_word(self, word: Word) -> None:
        """Updates an existing word in the database."""
        if word.id is None:
            raise ValueError("Word ID must be provided for update.")

        con = self.get_connection()
        cur = con.cursor()
        cur.execute(
            "UPDATE words SET kanji_word=?, kana_word=?, english_word=?, japanese_sentence=?, english_sentence=?, tag=? WHERE id=?",
            (
                word.kanji_word,
                word.kana_word,
                word.english_word,
                word.japanese_sentence,
                word.english_sentence,
                word.tag,
                word.id,
            ),
        )
        con.commit()
        con.close()

    def add_word(self, word: Word) -> None:
        """Adds a new word to the database."""
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO words (kanji_word, kana_word, english_word, japanese_sentence, english_sentence, tag) VALUES (?, ?, ?, ?, ?, ?)",
            (
                word.kanji_word,
                word.kana_word,
                word.english_word,
                word.japanese_sentence,
                word.english_sentence,
                word.tag,
            ),
        )
        con.commit()
        con.close()

    def record_result(self, word_id: int, correct: bool) -> None:
        """Records the result of a test."""
        # This is a placeholder for future logic (e.g. spaced repetition)
        con = self.get_connection()
        cur = con.cursor()
        # Check if exists
        cur.execute("SELECT id FROM last_tested WHERE word_id = ?", (word_id,))
        row = cur.fetchone()

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
