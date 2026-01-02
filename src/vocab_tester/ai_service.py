import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class AIServiceError(Exception):
    pass


class GeneratedWordData(BaseModel):
    kana_word: str = Field(
        description="The reading of the kanji word in hiragana or katakana"
    )
    english_word: str = Field(description="The English translation of the word")
    japanese_sentence: str = Field(
        description="A simple Japanese example sentence using the word"
    )
    english_sentence: str = Field(
        description="The English translation of the example sentence"
    )


class AIService:
    def __init__(self):
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise AIServiceError("API_KEY not found in environment variables")
        self.client = genai.Client(api_key=api_key)

    def generate_word_data(self, kanji_word: str) -> GeneratedWordData:
        prompt = f"""
        Generate vocabulary data for the Japanese word: {kanji_word}
        
        Requirements:
        1. Provide the kana reading.
        2. Provide a clear English translation.
        3. Provide a simple Japanese example sentence that demonstrates common usage.
        4. Provide the English translation of that sentence.
        
        Return the result ONLY as a JSON object with the following keys:
        - kana_word
        - english_word
        - japanese_sentence
        - english_sentence
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedWordData,
                ),
            )

            # The new SDK might return the object directly if schema is provided
            # but usually we parse from text for safety if it returns JSON string
            if hasattr(response, "parsed") and response.parsed:
                return response.parsed  # type: ignore

            data = json.loads(response.text)  # type: ignore
            return GeneratedWordData(**data)
        except Exception as e:
            raise AIServiceError(f"Failed to generate word data: {str(e)}")
