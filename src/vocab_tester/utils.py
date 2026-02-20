import sys
import ctypes
import platform
import subprocess
import base64
import re


def normalize_text(text: str) -> str:
    """
    Normalizes text by converting to lowercase and removing all spaces and punctuation.
    """
    # Remove all characters that are not letters or numbers
    # We use \w but that includes underscores, so let's be more specific if needed.
    # Actually, for English meanings, we probably just want to keep alphanumeric.
    # \W matches any non-alphanumeric character; equivalent to [^a-zA-Z0-9_].
    # Let's also remove underscores just in case.
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


def is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux (WSL)."""
    if sys.platform != "linux":
        return False
    try:
        release = platform.release().lower()
        return "microsoft" in release or "wsl" in release
    except Exception:
        return False


def _set_ime_wsl(enable: bool) -> None:
    """
    Toggle IME in WSL by calling powershell.exe.
    Uses P/Invoke via Add-Type to interact with Win32 APIs.
    Runs asynchronously via Popen to avoid blocking the UI.
    """
    # C# code to toggle IME via P/Invoke
    # Logic:
    # 1. Attach to the foreground window's thread to access its input state.
    # 2. Get the focused window (which might be a child of the main window).
    # 3. Get the Default IME Window associated with that focus.
    # 4. Send WM_IME_CONTROL message to set open status.
    csharp_code = """
using System;
using System.Runtime.InteropServices;
public class Ime {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")] public static extern IntPtr GetFocus();
    [DllImport("imm32.dll")] public static extern IntPtr ImmGetDefaultIMEWnd(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    
    private const uint WM_IME_CONTROL = 0x0283;
    private const int IMC_SETOPENSTATUS = 0x0006;

    public static void Set(bool open) {
        var hwnd = GetForegroundWindow();
        if(hwnd == IntPtr.Zero) return;
        
        uint processId;
        uint targetThreadId = GetWindowThreadProcessId(hwnd, out processId);
        uint currentThreadId = GetCurrentThreadId();
        
        bool attached = false;
        if(targetThreadId != currentThreadId) {
            attached = AttachThreadInput(currentThreadId, targetThreadId, true);
        }
        
        try {
            var hFocus = GetFocus();
            if (hFocus == IntPtr.Zero) hFocus = hwnd;

            var hImeWnd = ImmGetDefaultIMEWnd(hFocus);
            if (hImeWnd != IntPtr.Zero) {
                IntPtr wParam = (IntPtr)IMC_SETOPENSTATUS;
                IntPtr lParam = (IntPtr)(open ? 1 : 0);
                SendMessage(hImeWnd, WM_IME_CONTROL, wParam, lParam);
            }
        } finally {
            if(attached) {
                AttachThreadInput(currentThreadId, targetThreadId, false);
            }
        }
    }
}
"""
    # PowerShell command to compile and run
    # Use -TypeDefinition to compile the C# code
    ps_cmd = f"""
$code = @'
{csharp_code}
'@
Add-Type -TypeDefinition $code
[Ime]::Set(${"true" if enable else "false"})
"""

    # Encode as UTF-16LE for PowerShell -EncodedCommand
    encoded_cmd = base64.b64encode(ps_cmd.encode("utf-16le")).decode("utf-8")

    try:
        # Use Popen to run in background and avoid blocking the TUI
        subprocess.Popen(
            ["powershell.exe", "-EncodedCommand", encoded_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        # Fallback to full path if standard command fails
        try:
            subprocess.Popen(
                [
                    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-EncodedCommand",
                    encoded_cmd,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # PowerShell not found, cannot toggle IME


def set_ime_mode(enable: bool) -> None:
    """
    Sets the IME open status on Windows or WSL.
    enable=True -> Open IME (Japanese Input)
    enable=False -> Close IME (English/Direct Input)
    Does nothing on non-Windows/non-WSL platforms.
    """
    if sys.platform == "win32":
        try:
            # Get the window handle of the current application
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return

            # Get Input Method Context
            himc = ctypes.windll.imm32.ImmGetContext(hwnd)
            if not himc:
                return

            # Set Open Status
            # 1 = Open (Japanese), 0 = Closed (English)
            ctypes.windll.imm32.ImmSetOpenStatus(himc, 1 if enable else 0)

            # Release Context
            ctypes.windll.imm32.ImmReleaseContext(hwnd, himc)
        except Exception:
            # Fail silently to avoid crashing
            pass
    elif is_wsl():
        _set_ime_wsl(enable)
