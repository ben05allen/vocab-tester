from unittest.mock import MagicMock, patch
from vocab_tester.app import VocabTesterApp


class MockApp(VocabTesterApp):
    def __init__(self):
        super().__init__()
        # Mock notify since we can't display notifications in a headless test easily without running the full app loop
        self.notify = MagicMock()


def test_copy_to_clipboard_powershell_success():
    app = MockApp()

    with patch("shutil.which") as mock_which:
        # Simulate powershell.exe exists
        mock_which.side_effect = (
            lambda x: "/path/to/powershell.exe" if x == "powershell.exe" else None
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            mock_process.returncode = 0

            app.copy_to_clipboard("test text")

            expected_command = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "$ms = New-Object System.IO.MemoryStream; [Console]::OpenStandardInput().CopyTo($ms); $text = [System.Text.Encoding]::UTF8.GetString($ms.ToArray()); Set-Clipboard -Value $text",
            ]
            mock_popen.assert_called_with(expected_command, stdin=-1, close_fds=True)
            mock_process.communicate.assert_called_with(input=b"test text")
            app.notify.assert_called_with("Copied to clipboard (WSL)!")


def test_copy_to_clipboard_powershell_failure_fallback_to_clip():
    app = MockApp()

    with patch("shutil.which") as mock_which:
        # Both exist
        mock_which.side_effect = lambda x: "/path/to/" + x

        with patch("subprocess.Popen") as mock_popen:
            # First call (powershell) fails with exception
            mock_process_clip = MagicMock()
            mock_process_clip.returncode = 0

            mock_popen.side_effect = [Exception("Powershell failed"), mock_process_clip]

            app.copy_to_clipboard("test text")

            # We removed the error notification on silent fallback
            app.notify.assert_called_with("Copied to clipboard (WSL-clip)!")

            # Verify clip.exe was called
            args, _ = mock_popen.call_args
            assert args[0] == ["clip.exe"]


def test_copy_to_clipboard_no_wsl():
    app = MockApp()

    with patch("shutil.which", return_value=None):
        with patch("textual.app.App.copy_to_clipboard") as mock_super_copy:
            app.copy_to_clipboard("test text")

            mock_super_copy.assert_called_with("test text")
            app.notify.assert_called_with("Copied to clipboard!")
