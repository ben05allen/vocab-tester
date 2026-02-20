from unittest.mock import patch, MagicMock
from vocab_tester.wsl_utils import set_ime_mode, is_wsl


def test_is_wsl():
    with patch("sys.platform", "linux"):
        with patch(
            "platform.release", return_value="5.15.90.1-microsoft-standard-WSL2"
        ):
            assert is_wsl() is True
        with patch("platform.release", return_value="5.15.0-76-generic"):
            assert is_wsl() is False

    with patch("sys.platform", "darwin"):
        assert is_wsl() is False


def test_set_ime_mode_wsl():
    with patch("sys.platform", "linux"):
        with patch("vocab_tester.wsl_utils.is_wsl", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                set_ime_mode(True)
                mock_popen.assert_called_once()
                args, _ = mock_popen.call_args
                # Check for powershell execution
                assert args[0][0] == "powershell.exe"
                assert args[0][1] == "-EncodedCommand"
                # We can decode the encoded command to verify content if needed,
                # but simply checking it was called with powershell is sufficient
                # given the complexity of the encoded string.


def test_set_ime_mode_wsl_fallback():
    # Simulate first Popen raising FileNotFoundError, second succeeding
    with patch("sys.platform", "linux"):
        with patch("vocab_tester.wsl_utils.is_wsl", return_value=True):
            # First call raises, second returns mock
            side_effects = [FileNotFoundError, MagicMock()]
            with patch("subprocess.Popen", side_effect=side_effects) as mock_popen:
                set_ime_mode(True)
                # Should be called twice
                assert mock_popen.call_count == 2

                # First call
                args1, _ = mock_popen.call_args_list[0]
                assert args1[0][0] == "powershell.exe"

                # Second call (fallback)
                args2, _ = mock_popen.call_args_list[1]
                assert (
                    args2[0][0]
                    == "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
                )


def test_set_ime_mode_linux():
    # Should do nothing on linux (non-WSL)
    with patch("sys.platform", "linux"):
        # We assume is_wsl returns False for this test
        with patch("vocab_tester.wsl_utils.is_wsl", return_value=False):
            # We also need to mock ctypes just in case it tries to access it
            with patch("ctypes.windll", create=True) as mock_windll:
                set_ime_mode(True)
                mock_windll.user32.GetForegroundWindow.assert_not_called()


def test_set_ime_mode_windows():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll", create=True) as mock_windll:
            # Setup mocks
            mock_hwnd = 123
            mock_himc = 456
            mock_windll.user32.GetForegroundWindow.return_value = mock_hwnd
            mock_windll.imm32.ImmGetContext.return_value = mock_himc

            # Test Enable
            set_ime_mode(True)

            mock_windll.user32.GetForegroundWindow.assert_called_once()
            mock_windll.imm32.ImmGetContext.assert_called_once_with(mock_hwnd)
            mock_windll.imm32.ImmSetOpenStatus.assert_called_once_with(mock_himc, 1)
            mock_windll.imm32.ImmReleaseContext.assert_called_once_with(
                mock_hwnd, mock_himc
            )


def test_set_ime_mode_windows_disable():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll", create=True) as mock_windll:
            # Setup mocks
            mock_hwnd = 123
            mock_himc = 456
            mock_windll.user32.GetForegroundWindow.return_value = mock_hwnd
            mock_windll.imm32.ImmGetContext.return_value = mock_himc

            # Test Disable
            set_ime_mode(False)

            mock_windll.imm32.ImmSetOpenStatus.assert_called_once_with(mock_himc, 0)


def test_set_ime_mode_windows_no_window():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll", create=True) as mock_windll:
            # Setup mocks
            mock_windll.user32.GetForegroundWindow.return_value = None

            # Test
            set_ime_mode(True)

            mock_windll.user32.GetForegroundWindow.assert_called_once()
            mock_windll.imm32.ImmGetContext.assert_not_called()


def test_set_ime_mode_windows_exception():
    with patch("sys.platform", "win32"):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.user32.GetForegroundWindow.side_effect = Exception("Boom")

            # Should not raise
            set_ime_mode(True)
