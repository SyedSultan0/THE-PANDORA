"""Loader for the candidates dataset."""

from pathlib import Path

from pydantic import ValidationError

from app.loaders._json import DataLoadError, load_json_file
from app.models.candidates import Candidates

# Default location: <project_root>/data/candidates.json
DEFAULT_CANDIDATES_PATH = Path(__file__).resolve().parents[2] / "data" / "candidates.json"


def load_candidates(path: Path | None = None) -> Candidates:
    """Load, validate, and return the candidates dataset.

    Args:
        path: Optional explicit path to the candidates JSON file.
            Defaults to ``data/candidates.json`` relative to the project root.

    Returns:
        A validated :class:`Candidates` model.

    Raises:
        DataLoadError: If the file is missing, malformed, or fails schema
            validation.
    """
    file_path = path if path is not None else DEFAULT_CANDIDATES_PATH
    data = load_json_file(file_path)

    try:
        return Candidates.model_validate(data)
    except ValidationError as exc:
        raise DataLoadError(
            f"Candidates file '{file_path.name}' failed validation: {exc}"
        ) from exc