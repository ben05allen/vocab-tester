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

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

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

### Navigation

- **Quiz Screen:**
  - Type your answer and press `Enter`.
  - First prompt is for the **Kana reading**.
  - Second prompt is for the **English meaning**.
  - After the result is shown, press `Next` (or `Enter` if focused) to continue.
  - Click `Edit` to modify the current word.
  - Click `Add` to add a new word.
  - Click `Filter` to choose a specific tag to study.

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
