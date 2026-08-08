"""Loader for the curriculum dataset."""

from pathlib import Path

from pydantic import ValidationError

from app.loaders._json import DataLoadError, load_json_file
from app.models.curriculum import Curriculum

# Default location: <project_root>/data/curriculum.json
DEFAULT_CURRICULUM_PATH = Path(__file__).resolve().parents[2] / "data" / "curriculum.json"


def load_curriculum(path: Path | None = None) -> Curriculum:
    """Load, validate, and return the curriculum dataset.

    Args:
        path: Optional explicit path to the curriculum JSON file.
            Defaults to ``data/curriculum.json`` relative to the project root.

    Returns:
        A validated :class:`Curriculum` model.

    Raises:
        DataLoadError: If the file is missing, malformed, or fails schema
            validation.
    """
    file_path = path if path is not None else DEFAULT_CURRICULUM_PATH
    data = load_json_file(file_path)

    try:
        return Curriculum.model_validate(data)
    except ValidationError as exc:
        raise DataLoadError(
            f"Curriculum file '{file_path.name}' failed validation: {exc}"
        ) from exc