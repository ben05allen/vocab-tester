from .db import Database
from .models import Word


class QuizSession:
    def __init__(self, db: Database, tag_filter: str | None = None) -> None:
        self.db = db
        self.queue: list[int] = []
        self.current_word: Word | None = None
        self.current_tag_filter: str | None = tag_filter

    def set_tag_filter(self, tag_filter: str | None) -> None:
        self.current_tag_filter = tag_filter
        self.queue.clear()

    def next_question(self) -> Word | None:
        """
        Loads the next question. Refills the queue up to 10 if needed.
        Recursively skips deleted/invalid words, returning the loaded Word or None.
        """
        while True:
            needed = 10 - len(self.queue)
            if needed > 0:
                exclude_ids = list(self.queue)

                # 1. Fetch incorrect words first
                incorrect_ids = self.db.get_incorrect_word_ids(
                    limit=needed,
                    tag_filter=self.current_tag_filter,
                    exclude_ids=exclude_ids,
                )
                self.queue.extend(incorrect_ids)

                needed -= len(incorrect_ids)
                if needed > 0:
                    exclude_ids.extend(incorrect_ids)

                    # 2. Fetch random words for the rest
                    random_ids = self.db.get_random_word_ids(
                        limit=needed,
                        tag_filter=self.current_tag_filter,
                        exclude_ids=exclude_ids,
                    )
                    self.queue.extend(random_ids)

            if not self.queue:
                self.current_word = None
                return None

            word_id = self.queue.pop(0)
            self.current_word = self.db.get_word(word_id)
            if self.current_word:
                return self.current_word

    def record_result(self, overall_correct: bool) -> None:
        if not self.current_word or self.current_word.id is None:
            return

        self.db.record_result(self.current_word.id, overall_correct)

        # Re-queue the word at different positions to practice again
        # if not already in the queue a couple of times
        if not overall_correct and self.queue[1:].count(self.current_word.id) < 2:
            self.queue.insert(2, self.current_word.id)
            self.queue.insert(5, self.current_word.id)

    def test_again(self) -> Word | None:
        """Queues the current word at index 0 and returns the newly loaded question."""
        if self.current_word and self.current_word.id is not None:
            self.queue.insert(0, self.current_word.id)
            return self.next_question()
        return None
