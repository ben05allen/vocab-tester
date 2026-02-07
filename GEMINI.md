# Project Context: Kanji Vocab Tester

A Terminal User Interface (TUI) application built with Textual to help users practice Kanji vocabulary using a SQLite3 backend.

## ⚙️ Tech Stack & Tooling

- Language: Python 3.14+
- TUI Framework: Textual
- Package Manager: uv (using pyproject.toml for metadata)
- External Dependencies: mpg123 (for audio playback)
- Database: SQLite3
- Linting/Formatting: ruff
- Git Hooks: prek (pre-commit management)

## 🛠 Development Workflow

When helping me write code, please adhere to these commands:

- Ensure that new features are developed in a git branch separate from the main (or master) branch
- Environment Setup: `uv sync`
- Running the App: `uv run vocab-tester` (once entry points are defined)
- Linting: `uv run ruff check --fix && uv ruff format .`
- Pre-commit: Hooks are managed via prek.

## 🗄 Database Schema

The database schema is record in `ref/sqlite3-schema.txt`

## 📝 Coding Guidelines

1. This is a Python project with a SQLite3 database using the Textualize library for UI, and uv for dependencies and packaging.
1. Textual Best Practices: Use `.tcss` files for styling rather than inline styles. Use Bindings for navigation.
1. Type Hinting: Use PEP 484 type hints for all function signatures.
1. Database Access: Use context managers for SQLite connections to ensure they close properly.
1. New functionality and code edits MUST NOT happen in the main git branch. Before making any code changes ensure that we are not in the main branch.
1. All imports should be at the top of files.
1. There is no need to import older types such as `List` or `Tuple` from `typing`, just use the newer variants such as `list` or `tuple`.
1. Always prefer `| None` over `Optional[]`
1. Ruff: Ensure all code passes ruff default rules (no unused imports, proper spacing). Autofix any ruff checks by using the `--fix` flag and keep code formatted by running `ruff format`. This is also enforced by a pre-commit hook.
1. When adding new functionality ensure that appropriate pytest tests are added as well.
1. Only run `git add` or `git commit` commands if explicitly asked to do so, otherwise leave it to the human in the loop.
1. **Queue Management**: The quiz queue MUST store word IDs (`int`), not `Word` objects. This ensures data freshness if a word is edited while in the queue.
