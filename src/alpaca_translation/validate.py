"""Integrity checks for Alpaca-style datasets."""

from __future__ import annotations

from typing import Any, Iterable

from .detect import DEFAULT_FIELDS, contains_chinese


def validate_dataset(
    records: list[dict[str, Any]], fields: Iterable[str] = DEFAULT_FIELDS
) -> dict[str, Any]:
    selected_fields = tuple(fields)
    invalid_records = []
    chinese_fields = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            invalid_records.append(index)
            continue
        for field in selected_fields:
            if contains_chinese(record.get(field)):
                chinese_fields.append({"index": index, "field": field})

    return {
        "records": len(records),
        "invalid_record_indices": invalid_records,
        "remaining_chinese_fields": chinese_fields,
        "remaining_chinese_count": len(chinese_fields),
    }
