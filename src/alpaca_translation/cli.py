"""Command-line interface for the Alpaca translation pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .clean import clean_candidates
from .detect import DEFAULT_FIELDS, detect_candidates
from .io import load_json, write_json
from .merge import merge_translations
from .translate import create_google_translator, translate_candidates
from .validate import validate_dataset


def _fields(value: str) -> tuple[str, ...]:
    fields = tuple(field.strip() for field in value.split(",") if field.strip())
    if not fields:
        raise argparse.ArgumentTypeError("at least one field is required")
    return fields


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alpaca-translate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Find Chinese-containing fields")
    detect_parser.add_argument("--input", required=True)
    detect_parser.add_argument("--output", required=True)
    detect_parser.add_argument("--fields", type=_fields, default=DEFAULT_FIELDS)

    clean_parser = subparsers.add_parser("clean", help="Clean detected candidates")
    clean_parser.add_argument("--input", required=True)
    clean_parser.add_argument("--output", required=True)

    translate_parser = subparsers.add_parser("translate", help="Translate cleaned candidates")
    translate_parser.add_argument("--input", required=True)
    translate_parser.add_argument("--output", required=True)
    translate_parser.add_argument("--source", default="zh-CN")
    translate_parser.add_argument("--target", default="en")
    translate_parser.add_argument("--max-retries", type=_positive_int, default=3)
    translate_parser.add_argument("--delay", type=float, default=0.1)
    translate_parser.add_argument("--checkpoint-every", type=_positive_int, default=25)
    translate_parser.add_argument("--overwrite", action="store_true")

    merge_parser = subparsers.add_parser("merge", help="Merge translations into source data")
    merge_parser.add_argument("--original", required=True)
    merge_parser.add_argument("--translations", required=True)
    merge_parser.add_argument("--output", required=True)
    merge_parser.add_argument("--report", required=True)
    merge_parser.add_argument("--fields", type=_fields, default=DEFAULT_FIELDS)

    validate_parser = subparsers.add_parser("validate", help="Check dataset structure and language")
    validate_parser.add_argument("--input", required=True)
    validate_parser.add_argument("--report")
    validate_parser.add_argument("--fields", type=_fields, default=DEFAULT_FIELDS)

    return parser


def _require_record_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise TypeError("Alpaca input must be a JSON array")
    return value


def _run_detect(args: argparse.Namespace) -> int:
    records = _require_record_list(load_json(args.input))
    candidates = detect_candidates(records, args.fields)
    write_json(args.output, candidates)
    print(f"Found {len(candidates)} record(s) containing Chinese text.")
    return 0


def _run_clean(args: argparse.Namespace) -> int:
    value = load_json(args.input)
    if not isinstance(value, dict):
        raise TypeError("Candidate input must be a JSON object")
    cleaned = clean_candidates(value)
    write_json(args.output, cleaned)
    print(f"Kept {len(cleaned)} translation candidate(s).")
    return 0


def _run_translate(args: argparse.Namespace) -> int:
    value = load_json(args.input)
    if not isinstance(value, dict):
        raise TypeError("Candidate input must be a JSON object")

    output = Path(args.output)
    existing = None
    if output.exists() and not args.overwrite:
        existing = load_json(output)
        if not isinstance(existing, dict):
            raise TypeError("Existing translation output must be a JSON object")

    translator = create_google_translator(args.source, args.target)

    def checkpoint(result: dict, position: int, total: int) -> None:
        if position % args.checkpoint_every == 0 or position == total:
            write_json(output, result)
            print(f"Translated {position}/{total} pending record(s).")

    translated = translate_candidates(
        value,
        translator,
        existing=existing,
        max_retries=args.max_retries,
        delay=args.delay,
        progress=checkpoint,
    )
    write_json(output, translated)
    print(f"Translation output contains {len(translated)} record(s).")
    return 0


def _run_merge(args: argparse.Namespace) -> int:
    records = _require_record_list(load_json(args.original))
    translations = load_json(args.translations)
    if not isinstance(translations, dict):
        raise TypeError("Translation input must be a JSON object")
    merged, report = merge_translations(records, translations, fields=args.fields)
    write_json(args.output, merged)
    write_json(args.report, report)
    print(
        f"Merged {report['changed_fields']} field(s) across "
        f"{report['translated_records']} record(s)."
    )
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    records = _require_record_list(load_json(args.input))
    report = validate_dataset(records, args.fields)
    if args.report:
        write_json(args.report, report)
    print(
        f"Records: {report['records']}; "
        f"remaining Chinese fields: {report['remaining_chinese_count']}."
    )
    return 1 if report["invalid_record_indices"] else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "detect": _run_detect,
        "clean": _run_clean,
        "translate": _run_translate,
        "merge": _run_merge,
        "validate": _run_validate,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
