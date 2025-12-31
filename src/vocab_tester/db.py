import sqlite3
import time
from pathlib import Path


type WordEntry = tuple[int, str, str, str, str, str, str]

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
                "noun",
            ),
            (
                "猫",
                "猫がベッドで寝ています。",
                "ねこ",
                "cat",
                "The cat is sleeping on the bed.",
                "noun",
            ),
            ("食べる", "朝ご飯を食べる。", "たべる", "eat", "I eat breakfast.", "verb"),
            (
                "勉強",
                "日本語を勉強しています。",
                "べんきょう",
                "study",
                "I am studying Japanese.",
                "verb",
            ),
            (
                "食べる",
                "私は毎日リンゴを一個食べます。",
                "たべる",
                "eat",
                "I eat one apple every day.",
                "verb",
            ),
            (
                "日本語",
                "日本語の勉強はとても楽しいです。",
                "にほんご",
                "Japanesee",
                "Studying Japanese is very fun.",
                "noun",
            ),
            (
                "先生",
                "あの人は私の大学の先生です。",
                "せんせい",
                "teacher",
                "That person is my university teacher.",
                "noun",
            ),
            (
                "行く",
                "明日、友達と一緒に映画館に行きます。",
                "いく",
                "go",
                "I am going to the movie theater with a friend tomorrow.",
                "verb",
            ),
            (
                "読む",
                "寝る前にいつも本を読みます。",
                "よむ",
                "read",
                "I always read a book before going to bed.",
                "verb",
            ),
            (
                "水",
                "冷たい水が飲みたいです。",
                "みず",
                "water",
                "I want to drink cold water.",
                "noun",
            ),
            (
                "友達",
                "週末に友達と公園で遊びました。",
                "ともだち",
                "friend",
                "I played at the park with my friend on the weekend.",
                "noun",
            ),
            (
                "天気",
                "今日はとても良い天気ですね。",
                "てんき",
                "weather",
                "The weather is very nice today, isn't it?",
                "noun",
            ),
            (
                "新しい",
                "先週、新しい靴を買いました。",
                "あたらしい",
                "new",
                "I bought new shoes last week.",
                "adjective",
            ),
            (
                "時間",
                "約束のまで、まだ時間があります。",
                "じかん",
                "time",
                "There is still time until the appointment.",
                "noun",
            ),
            (
                "見る",
                "昨日、面白いテレビ番組を見ました。",
                "みる",
                "watch",
                "I watched an interesting TV program yesterday.",
                "verb",
            ),
            (
                "会社",
                "父は大きな会社で働いています。",
                "かいしゃ",
                "company",
                "My father works for a large company.",
                "noun",
            ),
        ]
        cur = con.cursor()
        cur.executemany(
            "INSERT INTO words (kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag) VALUES (?, ?, ?, ?, ?, ?)",
            samples,
        )
        con.commit()

    def get_random_word(self, tag_filter: str | None = None) -> WordEntry | None:
        """
        Returns a random word tuple:
        (id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag)
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
        return row

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
        return [row[0] for row in rows]

    def get_word(self, word_id: int) -> WordEntry | None:
        """
        Returns a word tuple by ID:
        (id, kanji_word, japanese_sentence, kana_word, english_word, english_sentence, tag)
        """
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM words WHERE id = ?", (word_id,))
        row = cur.fetchone()
        con.close()
        return row

    def update_word(
        self,
        word_id: int,
        kanji: str,
        kana: str,
        english: str,
        jp_sentence: str,
        en_sentence: str,
        tag: str = "none",
    ) -> None:
        """Updates an existing word in the database."""
        tag = tag.strip() or "none"
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(
            "UPDATE words SET kanji_word=?, kana_word=?, english_word=?, japanese_sentence=?, english_sentence=?, tag=? WHERE id=?",
            (kanji, kana, english, jp_sentence, en_sentence, tag, word_id),
        )
        con.commit()
        con.close()

    def add_word(
        self,
        kanji: str,
        kana: str,
        english: str,
        jp_sentence: str,
        en_sentence: str,
        tag: str = "none",
    ) -> None:
        """Adds a new word to the database."""
        tag = tag.strip() or "none"
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO words (kanji_word, kana_word, english_word, japanese_sentence, english_sentence, tag) VALUES (?, ?, ?, ?, ?, ?)",
            (kanji, kana, english, jp_sentence, en_sentence, tag),
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
