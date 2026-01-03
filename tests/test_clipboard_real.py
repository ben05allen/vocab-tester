import shutil
import subprocess
import pytest
from vocab_tester.app import VocabTesterApp


def get_clipboard_content():
    """Helper to read clipboard content using powershell."""
    if not shutil.which("powershell.exe"):
        return None
    try:
        # We also need to set output encoding for the read to be reliable in some envs
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard",
        ]
        result = subprocess.check_output(command)
        return result.decode("utf-8").strip()
    except Exception:
        return None


@pytest.mark.skipif(
    not shutil.which("powershell.exe"), reason="powershell.exe not found"
)
def test_real_clipboard_roundtrip_japanese():
    app = VocabTesterApp()

    # "Father works at a big company."
    test_phrase = "父は大きな会社で働いています。"

    # Attempt to copy
    app.copy_to_clipboard(test_phrase)

    # Read back
    clipboard_content = get_clipboard_content()

    # Assert
    assert clipboard_content is not None
    assert clipboard_content == test_phrase, (
        f"Expected '{test_phrase}', got '{clipboard_content}'"
    )
