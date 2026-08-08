"""Tests for the curriculum loader and models."""

import json

import pytest
from pydantic import ValidationError

from app.loaders._json import DataLoadError
from app.loaders.curriculum import DEFAULT_CURRICULUM_PATH, load_curriculum
from app.models.curriculum import Curriculum, CurriculumDay, CurriculumModule


class TestLoadCurriculumSuccess:
    """Tests for successful curriculum loading."""

    def test_loads_real_curriculum_file(self) -> None:
        """The real curriculum.json file should load into a Curriculum model."""
        curriculum = load_curriculum()

        assert isinstance(curriculum, Curriculum)
        assert curriculum.cohort
        assert len(curriculum.modules) == 8
        assert len(curriculum.days) == 31

    def test_default_path_resolves_to_data(self) -> None:
        """The default path should point at the real data directory."""
        assert DEFAULT_CURRICULUM_PATH.name == "curriculum.json"
        assert DEFAULT_CURRICULUM_PATH.parent.name == "data"
        assert DEFAULT_CURRICULUM_PATH.exists()

    def test_loads_with_explicit_path(self, tmp_path) -> None:
        """Loading via an explicit file path should work."""
        data = {"cohort": "Test", "modules": [], "days": []}
        p = tmp_path / "curriculum.json"
        p.write_text(json.dumps(data), encoding="utf-8")

        result = load_curriculum(p)
        assert isinstance(result, Curriculum)
        assert result.cohort == "Test"
        assert result.modules == []
        assert result.days == []

    def test_module_days_are_integer_ranges(self) -> None:
        """Modules should have day ranges that cover the full course."""
        curriculum = load_curriculum()
        covers = [
            d
            for module in curriculum.modules
            for d in range(module.days[0], module.days[1] + 1)
        ]
        assert covers == list(range(1, 32))

    def test_days_have_type_and_objectives(self) -> None:
        """Every day entry should have a valid type and objectives."""
        curriculum = load_curriculum()
        for day in curriculum.days:
            assert isinstance(day, CurriculumDay)
            assert day.type in {"SETUP", "BUILD", "AI_CORE", "SHIP_IT", "LEARN", "OPTIMIZE", "CAPSTONE"}
            assert isinstance(day.objectives, list)
            assert len(day.objectives) > 0

    def test_modules_are_typed(self) -> None:
        """Modules should be CurriculumModule instances."""
        curriculum = load_curriculum()
        for module in curriculum.modules:
            assert isinstance(module, CurriculumModule)


class TestCurriculumModelValidation:
    """Tests for the curriculum Pydantic model validation."""

    def test_invalid_day_range_raises(self) -> None:
        """A module with start > end should fail validation."""
        with pytest.raises(ValidationError, match="day range is invalid"):
            CurriculumModule(n=1, title="Bad", days=(5, 3))

    def test_invalid_day_type_raises(self) -> None:
        """An unknown day type should fail validation."""
        with pytest.raises(ValidationError, match="type"):
            CurriculumDay(day=1, title="x", type="UNKNOWN", tools=[], objectives=[])

    def test_negative_day_raises(self) -> None:
        """A day number below 1 should fail validation."""
        with pytest.raises(ValidationError):
            CurriculumDay(day=0, title="x", type="BUILD", tools=[], objectives=[])


class TestLoadCurriculumFailures:
    """Tests for curriculum loading failure behavior."""

    def test_missing_file_raises(self, tmp_path) -> None:
        """Loading a non-existent file should raise DataLoadError."""
        missing = tmp_path / "does-not-exist.json"
        with pytest.raises(DataLoadError, match="not found"):
            load_curriculum(missing)

    def test_invalid_json_raises(self, tmp_path) -> None:
        """Malformed JSON should raise DataLoadError with a clear message."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid json", encoding="utf-8")

        with pytest.raises(DataLoadError, match="Invalid JSON"):
            load_curriculum(bad)

    def test_top_level_not_object_raises(self, tmp_path) -> None:
        """A JSON array at the top level should raise DataLoadError."""
        p = tmp_path / "curriculum.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_curriculum(p)

    def test_missing_top_level_key_raises(self, tmp_path) -> None:
        """A missing required top-level key should raise DataLoadError."""
        p = tmp_path / "curriculum.json"
        p.write_text(json.dumps({"modules": [], "days": []}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_curriculum(p)

    def test_modules_not_list_raises(self, tmp_path) -> None:
        """A non-list 'modules' value should raise DataLoadError."""
        p = tmp_path / "curriculum.json"
        p.write_text(json.dumps({"cohort": "x", "modules": {}, "days": []}), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_curriculum(p)

    def test_module_missing_keys_raises(self, tmp_path) -> None:
        """A module missing required keys should raise DataLoadError."""
        p = tmp_path / "curriculum.json"
        data = {
            "cohort": "x",
            "modules": [{"n": 1}],  # missing title, days
            "days": [],
        }
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_curriculum(p)

    def test_day_missing_keys_raises(self, tmp_path) -> None:
        """A day entry missing required keys should raise DataLoadError."""
        p = tmp_path / "curriculum.json"
        data = {
            "cohort": "x",
            "modules": [],
            "days": [{"day": 1, "title": "x"}],  # missing type, tools, objectives
        }
        p.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DataLoadError, match="failed validation"):
            load_curriculum(p)