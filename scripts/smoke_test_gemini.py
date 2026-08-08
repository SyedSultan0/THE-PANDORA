"""Manual smoke test for the Gemini LLM provider.

This script is NOT run by pytest. Run it manually when a real Gemini API
key is available:

    python scripts/smoke_test_gemini.py

It loads ``.env`` from the project root (if present), sends a simple prompt,
and prints the response. Exits non-zero on failure.
"""

import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` is importable.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.llm import GeminiProvider  # noqa: E402
from app.llm.config import load_env  # noqa: E402
from app.llm.errors import LLMConfigurationError, LLMGenerationError  # noqa: E402


def main() -> int:
    load_env()

    if not os.getenv("GEMINI_API_KEY"):
        print(
            "No GEMINI_API_KEY found. Copy .env.example to .env and set "
            "GEMINI_API_KEY, then re-run this script.",
            file=sys.stderr,
        )
        return 1

    provider = GeminiProvider()
    try:
        reply = provider.generate("Say hello in exactly one sentence.")
    except LLMConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except LLMGenerationError as exc:
        print(f"Generation error: {exc}", file=sys.stderr)
        return 3

    print(f"Gemini reply: {reply}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())