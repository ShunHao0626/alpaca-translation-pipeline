"""Merge translated fields back into a copy of the source dataset."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from .detect import DEFAULT_FIELDS


def merge_translations(
    records: list[dict[str, Any]],
    translations: dict[str, dict[str, str]],
    *,
    fields: Iterable[str] = DEFAULT_FIELDS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return a translated copy and an integrity report."""

    allowed = set(fields)
    merged = deepcopy(records)
    changed_fields = 0

    for raw_index, translated_entry in translations.items():
        try:
            index = int(raw_index)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Translation key is not a record index: {raw_index!r}") from error
        if index < 0 or index >= len(merged):
            raise IndexError(f"Translation index {index} is outside the dataset")
        if not isinstance(translated_entry, dict):
            raise TypeError(f"Translation {raw_index} must be an object")

        for field, value in translated_entry.items():
            if field not in allowed:
                raise ValueError(f"Translation contains a disallowed field: {field}")
            if not isinstance(value, str):
                raise TypeError(f"Translated value for {raw_index}.{field} must be a string")
            if merged[index].get(field) != value:
                merged[index][field] = value
                changed_fields += 1

    report = {
        "input_records": len(records),
        "output_records": len(merged),
        "translated_records": len(translations),
        "changed_fields": changed_fields,
        "record_count_preserved": len(records) == len(merged),
    }
    return merged, report
