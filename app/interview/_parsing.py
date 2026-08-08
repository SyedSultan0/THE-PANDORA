"""Shared LLM output parsing helpers for interview components."""

import json
import re
from typing import Any


def parse_json_object(raw: str, error_cls: type[Exception]) -> dict[str, Any]:
    """Parse LLM output into a JSON object, tolerating markdown fences.

    Args:
        raw: The raw LLM output string.
        error_cls: The exception class to raise on invalid output.

    Returns:
        The parsed JSON object as a dict.

    Raises:
        error_cls: If the output is empty, not valid JSON, or not an object.
    """
    if not raw or not raw.strip():
        raise error_cls("LLM returned an empty response.")

    text = raw.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise error_cls(
            f"LLM output is not valid JSON: {exc.msg} (line {exc.lineno}, "
            f"column {exc.colno})."
        ) from exc

    if not isinstance(data, dict):
        raise error_cls(
            f"LLM output must be a JSON object, got {type(data).__name__}."
        )
    return data