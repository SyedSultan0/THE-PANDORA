"""Loader for the curriculum dataset."""

from pathlib import Path
from typing import Any

from app.loaders._json import DataLoadError, load_json_file

# Default location: <project_root>/data/curriculum.json
DEFAULT_CURRICULUM_PATH = Path(__file__).resolve().parents[2] / "data" / "curriculum.json"

_REQUIRED_TOP_LEVEL_KEYS = {"cohort", "modules", "days"}
_REQUIRED_MODULE_KEYS = {"n", "title", "days"}
_REQUIRED_DAY_KEYS = {"day", "title", "type", "tools", "objectives"}


def load_curriculum(path: Path | None = None) -> dict[str, Any]:
    """Load and return the parsed curriculum dataset.

    Args:
        path: Optional explicit path to the curriculum JSON file.
            Defaults to ``data/curriculum.json`` relative to the project root.

    Returns:
        The parsed curriculum as a dictionary with keys:
        ``cohort`` (str), ``modules`` (list), and ``days`` (list).

    Raises:
        DataLoadError: If the file is missing, malformed, or has an
            unexpected top-level structure.
    """
    file_path = path if path is not None else DEFAULT_CURRICULUM_PATH
    data = load_json_file(file_path)

    _validate_top_level(data, file_path)
    _validate_modules(data["modules"], file_path)
    _validate_days(data["days"], file_path)

    return data


def _validate_top_level(data: Any, file_path: Path) -> None:
    """Validate the top-level curriculum structure."""
    if not isinstance(data, dict):
        raise DataLoadError(
            f"Curriculum file '{file_path.name}' must be a JSON object, "
            f"got {type(data).__name__}."
        )

    missing = _REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise DataLoadError(
            f"Curriculum file '{file_path.name}' is missing required top-level "
            f"key(s): {', '.join(sorted(missing))}."
        )


def _validate_modules(modules: Any, file_path: Path) -> None:
    """Validate the modules list structure."""
    if not isinstance(modules, list):
        raise DataLoadError(
            f"Curriculum file '{file_path.name}': 'modules' must be a list, "
            f"got {type(modules).__name__}."
        )

    for i, module in enumerate(modules):
        if not isinstance(module, dict):
            raise DataLoadError(
                f"Curriculum file '{file_path.name}': modules[{i}] must be an "
                f"object, got {type(module).__name__}."
            )
        missing = _REQUIRED_MODULE_KEYS - module.keys()
        if missing:
            raise DataLoadError(
                f"Curriculum file '{file_path.name}': modules[{i}] is missing "
                f"required key(s): {', '.join(sorted(missing))}."
            )


def _validate_days(days: Any, file_path: Path) -> None:
    """Validate the days list structure."""
    if not isinstance(days, list):
        raise DataLoadError(
            f"Curriculum file '{file_path.name}': 'days' must be a list, "
            f"got {type(days).__name__}."
        )

    for i, day in enumerate(days):
        if not isinstance(day, dict):
            raise DataLoadError(
                f"Curriculum file '{file_path.name}': days[{i}] must be an "
                f"object, got {type(day).__name__}."
            )
        missing = _REQUIRED_DAY_KEYS - day.keys()
        if missing:
            raise DataLoadError(
                f"Curriculum file '{file_path.name}': days[{i}] is missing "
                f"required key(s): {', '.join(sorted(missing))}."
            )