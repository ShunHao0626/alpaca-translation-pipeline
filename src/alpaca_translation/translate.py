"""Translate candidate fields with bounded retry and resume support."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Protocol

from .detect import contains_chinese


class Translator(Protocol):
    def translate(self, text: str) -> str | None:
        """Translate one string."""


def create_google_translator(source: str = "zh-CN", target: str = "en") -> Translator:
    """Create the optional deep-translator Google backend."""

    try:
        from deep_translator import GoogleTranslator
    except ImportError as error:
        raise RuntimeError(
            "Google translation support is optional. "
            "Install it with: pip install -e '.[google]'"
        ) from error
    return GoogleTranslator(source=source, target=target)


def translate_text(
    text: str,
    translator: Translator,
    *,
    max_retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Translate one Chinese-containing value with exponential backoff."""

    if not contains_chinese(text):
        return text
    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            result = translator.translate(text)
            if not isinstance(result, str) or not result.strip():
                raise ValueError("translation backend returned an empty value")
            return result
        except Exception as error:  # Backends expose several exception types.
            last_error = error
            if attempt + 1 < max_retries:
                sleep(2**attempt)
    raise RuntimeError(f"translation failed after {max_retries} attempts") from last_error


def translate_candidates(
    candidates: dict[str, dict[str, str]],
    translator: Translator,
    *,
    existing: dict[str, dict[str, str]] | None = None,
    max_retries: int = 3,
    delay: float = 0.1,
    progress: Callable[[dict[str, dict[str, str]], int, int], None] | None = None,
) -> dict[str, dict[str, str]]:
    """Translate candidates, skipping indices already present in ``existing``."""

    if delay < 0:
        raise ValueError("delay must be non-negative")

    result = dict(existing or {})
    pending = [(key, value) for key, value in candidates.items() if key not in result]
    total = len(pending)

    for position, (index, entry) in enumerate(pending, start=1):
        result[index] = {
            field: translate_text(value, translator, max_retries=max_retries)
            for field, value in entry.items()
        }
        if progress is not None:
            progress(result, position, total)
        if delay and position < total:
            time.sleep(delay)
    return result
