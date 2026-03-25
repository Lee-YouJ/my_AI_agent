# My AI Agent

This project is an AI agent set up using the [`uv`](https://github.com/astral-sh/uv) package manager.

## Environment Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *macOS (Homebrew):*
   ```bash
   brew install uv
   ```

2. **Sync Dependencies**:
   Initialize the virtual environment and install dependencies defined in `pyproject.toml`.
   ```bash
   uv sync
   ```

3. **Run the Project**:
   Run the application seamlessly within the `uv` managed virtual environment:
   ```bash
   uv run main.py
   ```