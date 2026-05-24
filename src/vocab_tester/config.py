from typing import Self
from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass
class Config:
    default_filter: str | None = None
    translation_kana: str = "hiragana"

    @classmethod
    def from_file(cls, file: Path) -> Self:
        settings = {}
        if file.exists():
            try:
                with file.open("rb") as f:
                    settings = tomllib.load(f)
            except Exception as e:
                # Log or handle error if needed, for now just re-raise
                # but since we want it to be robust, maybe just default to empty settings?
                # Actually, the original code had 'raise e' for general exceptions.
                raise e
        return cls(**settings)
