import subprocess
import tempfile

from gtts import gTTS
from .wsl_utils import is_wsl


class AudioService:
    def play_japanese_sentence(self, sentence: str) -> None:
        """
        Generates Japanese speech audio from text using gTTS and plays it
        using appropriate system audio utility (mpg123 or ffplay.exe on WSL).
        """
        tts = gTTS(sentence, lang="ja")

        with tempfile.NamedTemporaryFile(suffix=".mp3") as f_mp3:
            tts.save(f_mp3.name)

            if is_wsl():
                win_path = (
                    subprocess.check_output(["wslpath", "-w", f_mp3.name])
                    .decode("utf-8")
                    .strip()
                )
                subprocess.run(
                    ["ffplay.exe", "-nodisp", "-autoexit", win_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )

            else:
                subprocess.run(
                    [
                        "mpg123",
                        "-q",
                        "-f",
                        "16384",
                        "-r",
                        "44100",
                        "-b",
                        "1024",
                        f_mp3.name,
                    ],
                    check=False,
                )
