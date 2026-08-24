"""Find Chinese text in selected fields of Alpaca records."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
DEFAULT_FIELDS = ("system", "instruction", "input", "output")


def contains_chinese(value: Any) -> bool:
    """Return whether a value contains a CJK ideograph used in Chinese text."""

    return isinstance(value, str) and bool(CJK_PATTERN.search(value))


def detect_candidates(
    records: list[dict[str, Any]], fields: Iterable[str] = DEFAULT_FIELDS
) -> dict[str, dict[str, str]]:
    """Return record-indexed fields that contain Chinese text."""

    selected_fields = tuple(fields)
    candidates: dict[str, dict[str, str]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"Record {index} must be an object")
        selected = {
            field: record[field]
            for field in selected_fields
            if field in record and contains_chinese(record[field])
        }
        if selected:
            candidates[str(index)] = selected
    return candidates
