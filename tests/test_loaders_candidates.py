"""Tests for the candidates loader and models."""

import json

import pytest
from pydantic import ValidationError

from app.loaders._json import DataLoadError
from app.loaders.candidates import DEFAULT_CANDIDATES_PATH, load_candidates
from app.models.candidates import (
    AttemptedMission,
    Candidate,
    Candidates,
    Member,
    Signals,
    SkippedMission,
)


class TestLoadCandidatesSuccess:
    """Tests for successful candidates loading."""

    def test_loads_real_candidates_file(self) -> None:
        """The real candidates.json file should load into a Candidates model."""
        candidates = load_candidates()

        assert isinstance(candidates, Candidates)
        # 20 candidates in the provided dataset
        assert len(candidates.candidates) == 20

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
        assert isinstance(result, Candidates)
        assert result.candidates == []

    def test_members_have_required_fields(self) -> None:
        """Every candidate member should be a typed Member model."""
        candidates = load_candidates()
        for cand in candidates.candidates:
            assert isinstance(cand.member, Member)
            assert isinstance(cand, Candidate)
            assert isinstance(cand.signals, Signals)

    def test_missions_are_typed_variants(self) -> None:
        """Missions should be either AttemptedMission or SkippedMission instances."""
        candidates = load_candidates()
        for cand in candidates.candidates:
            for mission in cand.missions:
                assert isinstance(mission, (AttemptedMission, SkippedMission))

    def test_attempted_missions_have_result_fields(self) -> None:
        """Attempted missions should have passed and attempts."""
        candidates = load_candidates()
        for cand in candidates.candidates:
            for mission in cand.missions:
                if isinstance(mission, AttemptedMission):
                    assert "passed" in mission.model_dump()
                    assert mission.attempts >= 1

    def test_skipped_missions_have_skipped_flag(self) -> None:
        """Skipped missions should have the skipped flag set to true."""
        candidates = load_candidates()
        for cand in candidates.candidates:
            for mission in cand.missions:
                if isinstance(mission, SkippedMission):
                    assert mission.skipped is True


class TestMissionRouting:
    """Tests for the passed vs skipped mission routing."""

    def test_attempted_mission_parses(self) -> None:
        """An attempted mission should parse into AttemptedMission."""
        mission = AttemptedMission.model_validate(
            {"day": 7, "title": "Embeddings Explained", "passed": True, "attempts": 1}
        )
        assert isinstance(mission, AttemptedMission)
        assert mission.passed is True
        assert mission.attempts == 1

    def test_failed_attempted_mission_parses(self) -> None:
        """A failed attempted mission (passed=False) should still parse."""
        mission = AttemptedMission.model_validate(
            {"day": 8, "title": "Vector Databases", "passed": False, "attempts": 4}
        )
        assert isinstance(mission, AttemptedMission)
        assert mission.passed is False
        assert mission.attempts == 4

    def test_skipped_mission_parses(self) -> None:
        """A skipped mission should parse into SkippedMission."""
        mission = SkippedMission.model_validate(
            {"day": 14, "title": "Fine-Tuning Concepts", "skipped": True}
        )
        assert isinstance(mission, SkippedMission)
        assert mission.skipped is True

    def test_candidate_mixes_skipped_and_attempted(self) -> None:
        """A candidate with both skipped and attempted missions should parse."""
        candidate = Candidate.model_validate(
            {
                "member": {
                    "id": "C1",
                    "name": "Test",
                    "jobRole": "Engineer",
                    "yearsExperience": 2,
                    "education": "BS",
                    "status": "COMPLETED",
                },
                "missions": [
                    {"day": 1, "title": "Setup", "passed": True, "attempts": 1},
                    {"day": 2, "title": "Skip Me", "skipped": True},
                    {"day": 3, "title": "Fail", "passed": False, "attempts": 3},
                ],
                "signals": {"commitDays": 5, "missionsCompleted": 2, "missionsFirstTry": 1},
            }
        )
        assert isinstance(candidate.missions[0], AttemptedMission)
        assert isinstance(candidate.missions[1], SkippedMission)
        assert isinstance(candidate.missions[2], AttemptedMission)
        assert candidate.missions[2].passed is False


class TestCandidateModelValidation:
    """Tests for candidate model validation failures."""

    def test_attempted_mission_missing_attempts_raises(self) -> None:
        """An attempted mission without attempts should fail validation."""
        with pytest.raises(ValidationError):
            AttemptedMission.model_validate(
                {"day": 7, "title": "x", "passed": True}  # missing attempts
            )

    def test_attempted_mission_missing_passed_raises(self) -> None:
        """An attempted mission without passed should fail validation."""
        with pytest.raises(ValidationError):
            AttemptedMission.model_validate(
                {"day": 7, "title": "x", "attempts": 1}  # missing passed
            )

    def test_skipped_mission_false_raises(self) -> None:
        """A skipped mission with skipped=False should fail validation."""
        with pytest.raises(ValidationError):
            SkippedMission.model_validate(
                {"day": 7, "title": "x", "skipped": False}
            )

    def test_negative_years_experience_raises(self) -> None:
        """Negative yearsExperience should fail validation."""
        with pytest.raises(ValidationError):
            Member(
                id="1",
                name="x",
                jobRole="y",
                yearsExperience=-1,
                education="z",
                status="ACTIVE",
            )

    def test_mission_day_zero_raises(self) -> None:
        """A mission day of 0 should fail validation."""
        with pytest.raises(ValidationError):
            AttemptedMission.model_validate(
                {"day": 0, "title": "x", "passed": True, "attempts": 1}
            )

    def test_negative_attempts_raises(self) -> None:
        """Negative attempts should fail validation."""
        with pytest.raises(ValidationError):
            AttemptedMission.model_validate(
                {"day": 1, "title": "x", "passed": True, "attempts": 0}
            )


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

        with pytest.raises(DataLoadError, match="failed validation"):
            load_candidates(p)

    def test_missing_top_level_key_raises(self, tmp_path) -> None:
        """A missing top-level 'candidates' key should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        p.write_text(json.dumps({"people": []}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_candidates(p)

    def test_candidates_not_list_raises(self, tmp_path) -> None:
        """A non-list 'candidates' value should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        p.write_text(json.dumps({"candidates": {}}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_candidates(p)

    def test_candidate_missing_keys_raises(self, tmp_path) -> None:
        """A candidate missing required keys should raise DataLoadError."""
        p = tmp_path / "candidates.json"
        data = {"candidates": [{"member": {}, "missions": []}]}  # missing signals
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
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

        with pytest.raises(DataLoadError, match="failed validation"):
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

        with pytest.raises(DataLoadError, match="failed validation"):
            load_candidates(p)