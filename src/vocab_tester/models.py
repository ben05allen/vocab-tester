from pydantic import BaseModel, Field, ConfigDict


class Word(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = Field(default=None, description="Database ID")
    kanji_word: str = Field(min_length=1)
    japanese_sentence: str = Field(min_length=1)
    kana_word: str = Field(min_length=1)
    english_word: str = Field(min_length=1)
    english_sentence: str = Field(min_length=1)
    tag: str = Field(default="none", min_length=1)
