"""Reusable curriculum lookup helpers.

These helpers operate on the loaded :class:`Curriculum` Pydantic model and
provide the day/module lookups the context builder and future Interview
Engine will need.
"""

from app.models.curriculum import Curriculum, CurriculumDay, CurriculumModule


def get_day(curriculum: Curriculum, day_number: int) -> CurriculumDay | None:
    """Return the curriculum day with the given day number, or ``None``.

    Args:
        curriculum: The loaded curriculum model.
        day_number: The 1-based day number to look up.

    Returns:
        The matching :class:`CurriculumDay`, or ``None`` if not found.
    """
    for day in curriculum.days:
        if day.day == day_number:
            return day
    return None


def get_module(curriculum: Curriculum, module_number: int) -> CurriculumModule | None:
    """Return the curriculum module with the given module number, or ``None``.

    Args:
        curriculum: The loaded curriculum model.
        module_number: The 1-based module number to look up.

    Returns:
        The matching :class:`CurriculumModule`, or ``None`` if not found.
    """
    for module in curriculum.modules:
        if module.n == module_number:
            return module
    return None


def module_day_numbers(module: CurriculumModule) -> list[int]:
    """Return the day numbers covered by a module.

    Module day ranges are inclusive: ``[1, 3]`` means days 1, 2, and 3.

    Args:
        module: The curriculum module.

    Returns:
        A sorted list of day numbers covered by the module.
    """
    start, end = module.days
    return list(range(start, end + 1))


def get_module_days(curriculum: Curriculum, module_number: int) -> list[CurriculumDay]:
    """Return the curriculum days belonging to a module.

    Args:
        curriculum: The loaded curriculum model.
        module_number: The 1-based module number.

    Returns:
        A list of :class:`CurriculumDay` objects in day order. Empty if the
        module number is unknown.
    """
    module = get_module(curriculum, module_number)
    if module is None:
        return []

    by_day = {day.day: day for day in curriculum.days}
    return [by_day[n] for n in module_day_numbers(module) if n in by_day]


def get_days_for_missions(
    curriculum: Curriculum, mission_days: list[int]
) -> list[CurriculumDay]:
    """Return the curriculum days that correspond to the given mission days.

    Args:
        curriculum: The loaded curriculum model.
        mission_days: A list of day numbers referenced by candidate missions.

    Returns:
        A list of :class:`CurriculumDay` objects in day order. Days not
        present in the curriculum are skipped.
    """
    by_day = {day.day: day for day in curriculum.days}
    return [by_day[n] for n in sorted(set(mission_days)) if n in by_day]