from pathlib import Path
import re

from jaconv import kata2hira, kata2alphabet
from sudachipy import Dictionary

from .config import Config

_config_path = Path("settings.toml")
CONFIG = Config.from_file(_config_path)
TOKENIZER = Dictionary().create()


def kanji_to_kana(text: str, *, kana_filter: str = "") -> str:
    if kana_filter == "":
        kana_filter = CONFIG.translation_kana

    tokens = TOKENIZER.tokenize(text)
    kana = " ".join(t.reading_form() for t in tokens)

    if kana_filter.lower() == "hiragana":
        return kata2hira(kana)
    elif kana_filter.lower() in ["romanji", "latin", "alphabet"]:
        return kata2alphabet(kana)

    return kana


def normalize_text(text: str) -> str:
    """
    Normalizes text by converting to lowercase and removing all spaces and punctuation.
    """
    # Remove all characters that are not letters or numbers
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9]", "", normalized)
    return normalized


def is_answer_correct(user_answer: str, correct_answers_str: str) -> bool:
    """
    Checks if the user's answer matches any of the semicolon-separated correct answers,
    ignoring case, spaces, and punctuation.
    """
    user_normalized = normalize_text(user_answer)
    if not user_normalized and user_answer.strip():
        # If the user typed something that becomes empty after normalization (e.g. just punctuation)
        # we just fail.
        # But usually, if they typed "...", it shouldn't match "word".
        return False

    correct_list = [a.strip() for a in correct_answers_str.split(";")]
    for correct in correct_list:
        if user_normalized == normalize_text(correct):
            return True
    return False
