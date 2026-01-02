import pytest
from unittest.mock import MagicMock, patch
from vocab_tester.ai_service import AIService, AIServiceError


def test_ai_service_initialization_no_api_key():
    with patch("os.getenv", return_value=None):
        with pytest.raises(AIServiceError, match="API_KEY not found"):
            AIService()


def test_ai_service_generate_word_data_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"kana_word": "がっこう", "english_word": "school", "japanese_sentence": "学校に行きます。", "english_sentence": "I go to school."}'
    mock_response.parsed = None
    mock_client.models.generate_content.return_value = mock_response

    with patch("os.getenv", return_value="fake_key"):
        with patch("google.genai.Client", return_value=mock_client):
            service = AIService()
            data = service.generate_word_data("学校")

            assert data.kana_word == "がっこう"
            assert data.english_word == "school"
            assert data.japanese_sentence == "学校に行きます。"
            assert data.english_sentence == "I go to school."


def test_ai_service_generate_word_data_failure():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API Error")

    with patch("os.getenv", return_value="fake_key"):
        with patch("google.genai.Client", return_value=mock_client):
            service = AIService()
            with pytest.raises(AIServiceError, match="Failed to generate word data"):
                service.generate_word_data("学校")
