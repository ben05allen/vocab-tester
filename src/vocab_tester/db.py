from contextlib import contextmanager
from pathlib import Path
import sqlite3
import time
from typing import Generator

from .models import Word
from .seeds import SAMPLES

DB_PATH = Path("data/vocab.db")
SCHEMA_PATH = Path("ref/sqlite3-schema.txt")


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_cursor(
        self, *, commit: bool = False
    ) -> Generator[sqlite3.Cursor, None, None]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row

        yield con.cursor()

        if commit:
            con.commit()

        con.close()

    def _init_db(self) -> None:
        """Initialize the database with schema if tables don't exist."""
        # Ensure schema file exists, if not, we can't init
        if not SCHEMA_PATH.exists():
            raise RuntimeError("Database schema missing")

        with self.get_cursor(commit=True) as cur:
            # Check if table exists
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='words'"
            )
            if not cur.fetchone():
                with open(SCHEMA_PATH, "r") as f:
                    schema = f.read()
                cur.executescript(schema)

                # seed databas with sample data
                cur.executemany(
                    "INSERT INTO words (kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag) VALUES (?, ?, ?, ?, ?, ?)",
                    SAMPLES,
                )

    def get_random_word(self, tag_filter: str | None = None) -> Word | None:
        """
        Returns a random word object.
        """

        with self.get_cursor() as cur:
            if tag_filter:
                cur.execute(
                    "SELECT * FROM words WHERE tag = ? ORDER BY RANDOM() LIMIT 1",
                    (tag_filter,),
                )
            else:
                cur.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")

            row = cur.fetchone()

        if row:
            return Word(**dict(row))

    def get_random_word_ids(
        self,
        limit: int,
        tag_filter: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[int]:
        """
        Returns a list of random word IDs.
        """
        query = "SELECT id FROM words WHERE 1=1"
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

        with self.get_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return [row["id"] for row in rows]

    def get_incorrect_word_ids(
        self,
        limit: int,
        tag_filter: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[int]:
        """
        Returns a list of word IDs that were last answered incorrectly.
        """

        query = """
            SELECT w.id
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

        with self.get_cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return [row["id"] for row in rows]

    def get_tags(self) -> list[str]:
        """
        Returns a list of all unique tags, ordered by the ID of the most recent word using that tag.
        """
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT tag, MAX(id) as max_id FROM words GROUP BY tag ORDER BY max_id DESC"
            )
            rows = cur.fetchall()

        return [row["tag"] for row in rows]

    def get_word(self, word_id: int) -> Word | None:
        """
        Returns a word object by ID.
        """
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM words WHERE id = ?", (word_id,))
            row = cur.fetchone()

        if row:
            return Word(**dict(row))

    def update_word(self, word: Word) -> None:
        """Updates an existing word in the database."""
        if word.id is None:
            raise ValueError("Word ID must be provided for update.")

        with self.get_cursor(commit=True) as cur:
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

    def add_word(self, word: Word) -> None:
        """Adds a new word to the database."""

        with self.get_cursor(commit=True) as cur:
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

    def record_result(self, word_id: int, correct: bool) -> None:
        """Records the result of a test."""
        # This is a placeholder for future logic (e.g. spaced repetition)
        with self.get_cursor(commit=True) as cur:
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
