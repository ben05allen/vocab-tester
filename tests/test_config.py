import pytest
from vocab_tester.config import Config


def test_config_defaults():
    """Test that Config has the expected defaults."""
    config = Config()
    assert config.default_filter is None
    assert config.translation_kana == "hiragana"


def test_config_from_file_not_exists(tmp_path):
    """Test loading config when the file does not exist."""
    config_path = tmp_path / "non_existent.toml"
    config = Config.from_file(config_path)
    assert config.default_filter is None
    assert config.translation_kana == "hiragana"


def test_config_from_file_valid(tmp_path):
    """Test loading config from a valid TOML file."""
    config_path = tmp_path / "settings.toml"
    config_path.write_text(
        'default_filter = "spring26"\ntranslation_kana = "katakana"', encoding="utf-8"
    )

    config = Config.from_file(config_path)
    assert config.default_filter == "spring26"
    assert config.translation_kana == "katakana"


def test_config_from_file_partial(tmp_path):
    """Test loading config from a TOML file with missing keys."""
    config_path = tmp_path / "settings.toml"
    config_path.write_text('default_filter = "spring26"', encoding="utf-8")

    config = Config.from_file(config_path)
    assert config.default_filter == "spring26"
    assert config.translation_kana == "hiragana"  # Default should remain


def test_config_from_file_invalid_toml(tmp_path):
    """Test that invalid TOML raises an error (as implemented)."""
    config_path = tmp_path / "settings.toml"
    config_path.write_text("invalid = toml = format", encoding="utf-8")

    with pytest.raises(Exception):
        Config.from_file(config_path)
