"""Loader for the candidates dataset."""

from pathlib import Path
from typing import Any

from app.loaders._json import DataLoadError, load_json_file

# Default location: <project_root>/data/candidates.json
DEFAULT_CANDIDATES_PATH = Path(__file__).resolve().parents[2] / "data" / "candidates.json"

_REQUIRED_TOP_LEVEL_KEYS = {"candidates"}
_REQUIRED_CANDIDATE_KEYS = {"member", "missions", "signals"}
_REQUIRED_MEMBER_KEYS = {"id", "name", "jobRole", "yearsExperience", "education", "status"}
_REQUIRED_MISSION_KEYS = {"day", "title"}
_REQUIRED_SIGNAL_KEYS = {"commitDays", "missionsCompleted", "missionsFirstTry"}


def load_candidates(path: Path | None = None) -> dict[str, Any]:
    """Load and return the parsed candidates dataset.

    Args:
        path: Optional explicit path to the candidates JSON file.
            Defaults to ``data/candidates.json`` relative to the project root.

    Returns:
        The parsed candidates as a dictionary with a single key:
        ``candidates`` (list).

    Raises:
        DataLoadError: If the file is missing, malformed, or has an
            unexpected top-level structure.
    """
    file_path = path if path is not None else DEFAULT_CANDIDATES_PATH
    data = load_json_file(file_path)

    _validate_top_level(data, file_path)
    _validate_candidates(data["candidates"], file_path)

    return data


def _validate_top_level(data: Any, file_path: Path) -> None:
    """Validate the top-level candidates structure."""
    if not isinstance(data, dict):
        raise DataLoadError(
            f"Candidates file '{file_path.name}' must be a JSON object, "
            f"got {type(data).__name__}."
        )

    missing = _REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise DataLoadError(
            f"Candidates file '{file_path.name}' is missing required top-level "
            f"key(s): {', '.join(sorted(missing))}."
        )


def _validate_candidates(candidates: Any, file_path: Path) -> None:
    """Validate the candidates list structure."""
    if not isinstance(candidates, list):
        raise DataLoadError(
            f"Candidates file '{file_path.name}': 'candidates' must be a list, "
            f"got {type(candidates).__name__}."
        )

    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise DataLoadError(
                f"Candidates file '{file_path.name}': candidates[{i}] must be an "
                f"object, got {type(candidate).__name__}."
            )
        missing = _REQUIRED_CANDIDATE_KEYS - candidate.keys()
        if missing:
            raise DataLoadError(
                f"Candidates file '{file_path.name}': candidates[{i}] is missing "
                f"required key(s): {', '.join(sorted(missing))}."
            )

        _validate_member(candidate["member"], i, file_path)
        _validate_missions(candidate["missions"], i, file_path)
        _validate_signals(candidate["signals"], i, file_path)


def _validate_member(member: Any, candidate_index: int, file_path: Path) -> None:
    """Validate a single candidate's member object."""
    if not isinstance(member, dict):
        raise DataLoadError(
            f"Candidates file '{file_path.name}': candidates[{candidate_index}].member "
            f"must be an object, got {type(member).__name__}."
        )

    missing = _REQUIRED_MEMBER_KEYS - member.keys()
    if missing:
        raise DataLoadError(
            f"Candidates file '{file_path.name}': candidates[{candidate_index}].member "
            f"is missing required key(s): {', '.join(sorted(missing))}."
        )


def _validate_missions(missions: Any, candidate_index: int, file_path: Path) -> None:
    """Validate a single candidate's missions list."""
    if not isinstance(missions, list):
        raise DataLoadError(
            f"Candidates file '{file_path.name}': candidates[{candidate_index}].missions "
            f"must be a list, got {type(missions).__name__}."
        )

    for j, mission in enumerate(missions):
        if not isinstance(mission, dict):
            raise DataLoadError(
                f"Candidates file '{file_path.name}': candidates[{candidate_index}]."
                f"missions[{j}] must be an object, got {type(mission).__name__}."
            )
        missing = _REQUIRED_MISSION_KEYS - mission.keys()
        if missing:
            raise DataLoadError(
                f"Candidates file '{file_path.name}': candidates[{candidate_index}]."
                f"missions[{j}] is missing required key(s): "
                f"{', '.join(sorted(missing))}."
            )


def _validate_signals(signals: Any, candidate_index: int, file_path: Path) -> None:
    """Validate a single candidate's signals object."""
    if not isinstance(signals, dict):
        raise DataLoadError(
            f"Candidates file '{file_path.name}': candidates[{candidate_index}].signals "
            f"must be an object, got {type(signals).__name__}."
        )

    missing = _REQUIRED_SIGNAL_KEYS - signals.keys()
    if missing:
        raise DataLoadError(
            f"Candidates file '{file_path.name}': candidates[{candidate_index}].signals "
            f"is missing required key(s): {', '.join(sorted(missing))}."
        )