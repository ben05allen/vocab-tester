import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import Annotated

load_dotenv()


# Defining annotated types
KanaStr = Annotated[
    str, Field(description="The kana reading of the kanji word", min_length=1)
]
EnglishStr = Annotated[
    str, Field(description="The English translation of the word", min_length=1)
]
JpSentence = Annotated[
    str,
    Field(
        description="A simple Japanese example sentence using the word", min_length=1
    ),
]
EnSentence = Annotated[
    str,
    Field(description="The English translation of the example sentence", min_length=1),
]


class AIServiceError(Exception):
    pass


class GeneratedWordData(BaseModel):
    kana_word: KanaStr
    english_word: EnglishStr
    japanese_sentence: JpSentence
    english_sentence: EnSentence


class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise AIServiceError("API_KEY not found in environment variables")
        self.agent = Agent(
            model="google:gemini-3.1-flash-lite",
            output_type=GeneratedWordData,
        )

    def generate_word_data(self, kanji_word: str) -> GeneratedWordData:
        prompt = f"""
        Generate vocabulary data for the Japanese word: {kanji_word}

        Requirements:
        1. Provide the kana reading.
        2. Provide a clear English translation.
        3. Provide a simple Japanese example sentence that demonstrates common usage.
        4. Provide the English translation of that sentence.

        Return the result with the following keys:
        - kana_word
        - english_word
        - japanese_sentence
        - english_sentence
        """

        try:
            result = self.agent.run_sync(user_prompt=prompt)
            return result.output  # type: ignore
        except Exception as e:
            raise AIServiceError(f"Failed to generate word data: {str(e)}")
