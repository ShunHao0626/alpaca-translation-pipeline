"""Clean detected translation candidates without losing record alignment."""

from __future__ import annotations

from typing import Any

from .detect import contains_chinese


def clean_candidates(candidates: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Keep only non-empty string fields that still contain Chinese text.

    Record indices are deliberately preserved. Identical text in two records is
    not removed because both records must still receive the translated value.
    """

    cleaned: dict[str, dict[str, str]] = {}
    for raw_index, raw_entry in candidates.items():
        try:
            index = str(int(raw_index))
        except (TypeError, ValueError) as error:
            raise ValueError(f"Candidate key is not a record index: {raw_index!r}") from error
        if not isinstance(raw_entry, dict):
            raise TypeError(f"Candidate {raw_index} must be an object")

        entry = {
            str(field): value.strip()
            for field, value in raw_entry.items()
            if isinstance(value, str) and value.strip() and contains_chinese(value)
        }
        if entry:
            cleaned[index] = entry
    return cleaned
