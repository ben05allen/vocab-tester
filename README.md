# Kanji Vocab Tester

A terminal-based application (TUI) designed to help you practice Japanese Kanji vocabulary. Built with Python and Textual, it offers a keyboard-centric interface for Kanji study sessions.

## 🚀 Features

- **Interactive Quiz Mode:** Test your knowledge of Kanji readings (Kana) and meanings (English).
- **Vocabulary Management:** Easily add new words and edit existing entries directly from the terminal.
- **Tagging System:** Organize your vocabulary with custom tags (e.g., "verbs", "adjectives", "JLPT-N5") and filter your quiz sessions by these tags.
- **Smart Review:** Incorrect answers are automatically re-queued during the session to reinforce learning.
- **SQLite Backend:** Your progress and data are safely stored in a local SQLite database.

## 🛠️ Tech Stack

- **Language:** Python 3.14+
- **UI Framework:** [Textual](https://textual.textualize.io/)
- **Database:** Local SQLite3 (stays on your PC)
- **Data Validation:** Pydantic
- **Package Manager:** uv
- **Git Hooks:** prek

## 📦 Installation & Setup

### Prerequisites

- **Python 3.14+**
- **uv** (Python package manager)
- **mpg123**: Required for audio playback of example sentences.
  - Ubuntu/Debian: `sudo apt install mpg123`
  - macOS: `brew install mpg123`

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ben05allen/vocab-tester.git
   cd vocab-tester
   ```

2. **Sync dependencies:**

   ```bash
   uv sync
   ```

## 🎮 Usage

**Run the application:**

```bash
uv run vocab-tester
```

### Navigation & Controls

The application is designed to be keyboard-centric:

- **Quiz Flow:**
  1. **Reading:** Type the Kana reading and press `Enter`.
  2. **Meaning:** Type the English meaning and press `Enter`.
      - _Note:_ Multiple meanings can be stored (semicolon-separated). Any one of them is accepted as correct.
  3. **Result:** View corrections. Press `Next` (or `Enter` if focused) to continue.

- **Keyboard Shortcuts:**
  - `a`: **Add** a new word.
  - `e`: **Edit** the current word (active on result screen).
  - `d`: Toggle **Dark/Light** mode.
  - `q`: **Quit** the application.

- **Mouse:**
  - You can click buttons like `Filter`, `Next`, or `Copy` (appears on result screen).

## 💻 Development

1. **Run Tests:**

   ```bash
   uv run pytest
   ```

2. **Linting & Formatting:**

   ```bash
   uv run ruff check --fix
   uv run ruff format .
   ```

3. **Pre-commit Hooks:**
   This project uses `prek` to manage git hooks. Hooks are configured to run linting and formatting checks automatically to maintain code quality.

## 🙏 Acknowledgements

This project stands on the shoulders of several fantastic open-source libraries:

- **[Textualize](https://github.com/Textualize/textual)**: Powering the beautiful terminal interface.
- **[Pydantic](https://github.com/pydantic/pydantic)**: Handling robust data validation and modeling.
- **[pytest](https://github.com/pytest-dev/pytest)**: Ensuring the reliability of our codebase through testing.
- **[uv](https://github.com/astral-sh/uv)**: An extremely fast Python package and project manager, written in Rust.

If you find this application useful, please consider contributing to or supporting these incredible projects.

### 🤖 Built with Gemini

The vast majority of this application's code and architectural refactors were generated and implemented by **Gemini**, demonstrating the power of AI-assisted software engineering.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
