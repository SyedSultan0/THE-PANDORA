"""Shared JSON file loading utilities."""

import json
from pathlib import Path
from typing import Any


class DataLoadError(Exception):
    """Raised when a data file cannot be loaded or parsed."""


def load_json_file(path: Path) -> Any:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        The parsed JSON content.

    Raises:
        DataLoadError: If the file is missing or contains invalid JSON.
    """
    if not path.exists():
        raise DataLoadError(f"Data file not found: {path}")

    if not path.is_file():
        raise DataLoadError(f"Data path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise DataLoadError(
            f"Invalid JSON in data file '{path.name}': {exc.msg} (line {exc.lineno}, "
            f"column {exc.colno})"
        ) from exc