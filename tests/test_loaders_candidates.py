"""Tests for the candidates loader."""

import json

import pytest

from app.loaders._json import DataLoadError
from app.loaders.candidates import DEFAULT_CANDIDATES_PATH, load_candidates


class TestLoadCandidatesSuccess:
    """Tests for successful candidates loading."""

    def test_loads_real_candidates_file(self) -> None:
        """The real candidates.json file should load with the expected structure."""
        candidates = load_candidates()

        assert isinstance(candidates, dict)
        assert "candidates" in candidates
        # 20 candidates in the provided dataset
        assert len(candidates["candidates"]) == 20

    def test_default_path_resolves_to_data(self) -> None:
        """The default path should point at the real data directory."""
        assert DEFAULT_CANDIDATES_PATH.name == "candidates.json"
        assert DEFAULT_CANDIDATES_PATH.parent.name == "data"
        assert DEFAULT_CANDIDATES_PATH.exists()

    def test_loads_with_explicit_path(self, tmp_path) -> None:
        """Loading via an explicit file path should work."""
        data = {"candidates": []}
        p = tmp_path / "candidates.json"
        p.write_text(json.dumps(data), encoding="utf-8")

        result = load_candidates(p)
        assert result == data

    def test_members_have_required_fields(self) -> None:
        """Every candidate member should have the documented fields."""
        candidates = load_candidates()
        for cand in candidates["candidates"]:
            member = cand["member"]
            for key in ("id", "name", "jobRole", "yearsExperience", "education", "status"):
                assert key in member, f"Missing {key} in {member}"

    def test_missions_have_day_and_title(self) -> None:
        """Every mission should have day and title fields."""
        candidates = load_candidates()
        for cand in candidates["candidates"]:
            for mission in cand["missions"]:
                assert "day" in mission
                assert "title" in mission

    def test_signals_have_expected_keys(self) -> None:
        """Every candidate should have the three signal metrics."""
        candidates = load_candidates()
        for cand in candidates["candidates"]:
            signals = cand["signals"]
            for key in ("commitDays", "missionsCompleted", "missionsFirstTry"):
                assert key in signals


class TestLoadCandidatesFailures:
    """Tests for candidates loading failure behavior."""

    def test_missing_file_raises(self, tmp_path) -> None:
        """Loading a non-existent file should raise DataLoadError."""
        missing = tmp_path / "does-not-exist.json"
        with pytest.raises(DataLoadError, match="not found"):
            load_candidates(missing)

    def test_invalid_json_raises(self, tmp_path) -> None:
        """Malformed JSON should raise DataLoadError with a clear message."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ not valid", encoding="utf-8")

        with pytest.raises(DataLoadError, match="Invalid JSON"):
            load_candidates(bad)

    def test_top_level_not_object_raises(self, tmp_path) -> None:
        """A JSON array at the top level should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        p.write_text("[1, 2]", encoding="utf-8")

        with pytest.raises(DataLoadError, match="must be a JSON object"):
            load_candidates(p)

    def test_missing_top_level_key_raises(self, tmp_path) -> None:
        """A missing top-level 'candidates' key should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        p.write_text(json.dumps({"people": []}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="missing required top-level key"):
            load_candidates(p)

    def test_candidates_not_list_raises(self, tmp_path) -> None:
        """A non-list 'candidates' value should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        p.write_text(json.dumps({"candidates": {}}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="'candidates' must be a list"):
            load_candidates(p)

    def test_candidate_missing_keys_raises(self, tmp_path) -> None:
        """A candidate missing required keys should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        data = {"candidates": [{"member": {}, "missions": []}]}  # missing signals
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="candidates\\[0\\].*missing required key"):
            load_candidates(p)

    def test_member_missing_keys_raises(self, tmp_path) -> None:
        """A member missing required keys should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        data = {
            "candidates": [
                {
                    "member": {"id": "1"},  # missing name, jobRole, etc.
                    "missions": [],
                    "signals": {"commitDays": 1, "missionsCompleted": 1, "missionsFirstTry": 1},
                }
            ]
        }
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="member.*missing required key"):
            load_candidates(p)

    def test_signals_missing_keys_raises(self, tmp_path) -> None:
        """A signals object missing required keys should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        data = {
            "candidates": [
                {
                    "member": {"id": "1", "name": "x", "jobRole": "y", "yearsExperience": 1,
                                "education": "z", "status": "ACTIVE"},
                    "missions": [],
                    "signals": {"commitDays": 1},  # missing the other two
                }
            ]
        }
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="signals.*missing required key"):
            load_candidates(p)