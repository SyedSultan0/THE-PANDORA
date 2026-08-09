"""Shared LLM output parsing helpers for interview components."""

from __future__ import annotations

import json
import re
from typing import Any


class _ParseError(Exception):
    """Internal parse failure with a human-readable reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


REPAIR_INSTRUCTION = (
    "Your previous response could not be parsed as valid JSON. "
    "Respond with ONLY a valid JSON object (no markdown fences, no surrounding text) "
    "matching the requested schema."
)


def generate_json(
    llm,
    prompt: str,
    error_cls: type[Exception],
    *,
    max_retries: int = 1,
    repair_prompt_suffix: str = REPAIR_INSTRUCTION,
) -> dict[str, Any]:
    """Call ``llm.generate`` and parse JSON, retrying once on parse failure.

    Args:
        llm: An LLMProvider instance.
        prompt: The prompt to send.
        error_cls: Exception class to raise if parsing ultimately fails.
        max_retries: Number of additional attempts after the first failure.
        repair_prompt_suffix: Instruction appended to the prompt on retry.

    Returns:
        Parsed JSON object.

    Raises:
        error_cls: If all attempts fail to produce valid JSON.
        LLMError: If the underlying provider fails.
    """
    last_error: Exception | None = None
    current_prompt = prompt
    for attempt in range(1 + max_retries):
        try:
            raw = llm.generate(current_prompt)
        except Exception as exc:
            # Propagate provider errors immediately.
            raise

        try:
            return parse_json_object(raw, error_cls)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                current_prompt = f"{prompt}\n\n{repair_prompt_suffix}"
                continue
            break

    raise last_error or error_cls("LLM output could not be parsed.")


def parse_json_object(raw: str, error_cls: type[Exception]) -> dict[str, Any]:
    """Parse LLM output into a JSON object, tolerating common LLM artifacts.

    The parser handles:
    - Markdown code fences (\\`\\`\\`json ... \\`\\`\\`)
    - Leading/trailing whitespace
    - A JSON object embedded in surrounding prose (first \\{ ... last \\})
    - Malformed JSON that becomes valid after stripping artifacts

    Args:
        raw: The raw LLM output string.
        error_cls: The exception class to raise on invalid output.

    Returns:
        The parsed JSON object as a dict.

    Raises:
        error_cls: If the output cannot be interpreted as a JSON object after
            all recovery attempts.
    """
    if not raw or not raw.strip():
        raise error_cls("LLM returned an empty response.")

    text = raw.strip()

    # 1. Strip markdown fences.
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. Try direct parse.
    data = _try_parse_json(text)
    if data is not None:
        return data

    # 2a. If direct parse produced valid JSON but not a dict, report that
    #     explicitly (preserves the original "must be a JSON object" message
    #     expected by existing tests).
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if parsed is not None and not isinstance(parsed, dict):
        raise error_cls(
            f"LLM output must be a JSON object, got {type(parsed).__name__}."
        )

    # 3. Try to extract the first JSON object from surrounding prose.
    #    Many LLMs wrap the JSON in explanatory text.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        data = _try_parse_json(candidate)
        if data is not None:
            return data

    # 4. All recovery attempts failed.
    raise error_cls(
        "LLM output is not valid JSON: Expecting value "
        "(the response could not be parsed as a JSON object)."
    )


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """Attempt to parse text as a JSON object; return None on failure."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data
