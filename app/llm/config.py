"""Configuration loading for LLM providers.

Loads environment variables from a ``.env`` file at the project root (if
present) so that providers can read configuration via ``os.getenv``.
"""

from pathlib import Path

from dotenv import load_dotenv

# Default location: <project_root>/.env
DEFAULT_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_env(path: Path | None = None) -> None:
    """Load environment variables from a ``.env`` file.

    Args:
        path: Optional explicit path to the ``.env`` file. Defaults to
            ``<project_root>/.env``. Missing files are ignored.
    """
    file_path = path if path is not None else DEFAULT_DOTENV_PATH
    if file_path.exists():
        load_dotenv(file_path)