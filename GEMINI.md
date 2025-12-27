# Project Context: Kanji Vocab Tester

A Terminal User Interface (TUI) application built with Textual to help users practice Kanji vocabulary using a SQLite3 backend.

## ⚙️ Tech Stack & Tooling

- Language: Python 3.14+
- TUI Framework: Textual
- Package Manager: uv (using pyproject.toml for metadata)
- Database: SQLite3
- Linting/Formatting: ruff
- Git Hooks: prek (pre-commit management)

## 📁 Project Structure

The project follows the standard "src" layout for packaged Python applications:

vocab-tester/
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Lockfile for reproducible builds
├── .pre-commit-config.yaml  # Pre-commit configuration
├── GEMINI.md                # (This file) Context for AI
├── src/
│   └── vocab_tester/
│       ├── __init__.py
│       ├── main.py          # App entry point
│       ├── db.py            # SQLite logic
│       └── styles.tcss      # Textual CSS
├── ref/
│   └── sqlite3-schema.txt   # Database schema definition
└── data/
    └── vocab.db             # SQLite database file (created at runtime)

## 🛠 Development Workflow

When helping me write code, please adhere to these commands:

- Environment Setup: uv sync
- Running the App: `uv run vocab-tester` (once entry points are defined)
- Linting: uv run ruff check .
- Pre-commit: Hooks are managed via prek.

## 🗄 Database Schema

The database schema is record in `ref/sqlite3-schema.txt`

## 📝 Coding Guidelines

1. Textual Best Practices: Use `.tcss` files for styling rather than inline styles. Use Bindings for navigation.
2. Type Hinting: Use PEP 484 type hints for all function signatures.
3. Database Access: Use context managers for SQLite connections to ensure they close properly.
4. Ruff: Ensure all code passes ruff default rules (no unused imports, proper spacing).
