# Alpaca Translation Pipeline

**English** · [简体中文](README_CN.md)

Alpaca Translation Pipeline is a reproducible workflow for identifying,
cleaning, translating, and reintegrating Chinese text in Alpaca-style instruction
datasets. It was created from an earlier one-off data-cleaning project and has been
refactored into a small command-line tool with tests and explicit provenance.

The repository is intended to contain processing code and small examples. The
original and translated full datasets will not be redistributed until their source
license and publication rights have been verified.

## Project status

The historical pipeline successfully produced a translated working copy. This
repository consolidates that work into an installable command-line tool with atomic
JSON writes, resumable translation output, merge-integrity reports, and tests.

| Stage | Current package |
| --- | --- |
| Chinese-text detection | `detect`, configurable fields, tested |
| Candidate cleanup | `clean`, keeps record indices aligned |
| Translation and retry handling | `translate`, Google backend, bounded retries, checkpoint and resume |
| Merge into original dataset | `merge`, writes a copy plus a count report |
| Dataset check | `validate`, reports remaining Chinese fields |
| Automated tests | Included; no network required |

## Why this project exists

Instruction datasets may contain mixed-language entries even when they are expected
to be primarily English. Translating the entire dataset wastes requests, changes
already valid content, and makes failures difficult to audit. This pipeline narrows
the work to Chinese-containing fields and preserves the rest of each record.

## Pipeline

```text
Alpaca JSON input
      |
      v
Detect Chinese-containing fields
      |
      v
Remove empty and non-Chinese candidate fields (duplicates are kept)
      |
      v
Translate the detected fields with bounded retries
      |
      v
Merge translated fields into a copy of the original dataset
      |
      v
Check record structure and report remaining Chinese text
```

Every stage writes a new artifact. The tool does not check whether an output path
equals an input path, so choose output paths that keep the original input intact.

## Expected input format

The default schema follows the common Alpaca record structure:

```json
[
  {
    "system": "",
    "instruction": "",
    "input": "",
    "output": ""
  }
]
```

By default the `system`, `instruction`, `input`, and `output` fields are scanned.
`detect`, `merge`, and `validate` accept `--fields` with a comma-separated list to
choose other string fields.

## Historical working snapshot

The local research copy used to design this project contains:

| Artifact | Entries |
| --- | ---: |
| Original Alpaca-style dataset | 37,168 |
| Raw extracted Chinese paths/objects | 10,623 |
| Cleaned translation candidates | 3,928 |
| Final merged dataset | 37,168 |

These numbers document the historical experiment; they are not a guarantee about
future input datasets.

## Repository layout

```text
alpaca-translation-pipeline/
├── src/alpaca_translation/
│   ├── __main__.py
│   ├── cli.py
│   ├── clean.py
│   ├── detect.py
│   ├── io.py
│   ├── merge.py
│   ├── translate.py
│   └── validate.py
├── data/
│   └── samples/
├── tests/
├── pyproject.toml
└── README.md
```

Large inputs, outputs, logs, and checkpoints should remain outside the repository.

## Installation

Create an isolated environment and install the package:

```bash
git clone https://github.com/ShunHao0626/alpaca-translation-pipeline.git
cd alpaca-translation-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[google]'
```

The `google` extra installs `deep-translator`. Detection, cleanup, merge, validation,
and the test suite do not require network access or a translation dependency.

## Command-line interface

The installed console command `alpaca-translate` is equivalent to
`python -m alpaca_translation`.

```bash
# Find records containing Chinese text.
python -m alpaca_translation detect \
  --input dataset.json \
  --output work/candidates.json

# Drop empty or non-Chinese candidate fields. Identical text in different
# records is deliberately kept so that every record receives its translation.
python -m alpaca_translation clean \
  --input work/candidates.json \
  --output work/candidates-cleaned.json

# Translate the candidate fields. Progress is checkpointed every 25 records
# (--checkpoint-every); rerunning with the same --output resumes, and
# --overwrite starts again. --max-retries and --delay are also available.
python -m alpaca_translation translate \
  --input work/candidates-cleaned.json \
  --output work/candidates-translated.json \
  --source zh-CN \
  --target en

# Merge translations into a copy of the original dataset.
python -m alpaca_translation merge \
  --original dataset.json \
  --translations work/candidates-translated.json \
  --output work/dataset-translated.json \
  --report work/merge-report.json

# Check record structure and list any fields that still contain Chinese text.
python -m alpaca_translation validate \
  --input work/dataset-translated.json \
  --report work/validate-report.json
```

## Safety and validation rules

Implemented in the current package:

- JSON is written atomically through a temporary file, so an interrupted write does
  not leave a truncated output.
- Merging works on a deep copy, preserves record order and total record count, and
  rejects out-of-range indices and fields outside the selected field list.
- Fields that were not selected for translation are left unchanged.
- Translation progress is checkpointed so interrupted jobs can resume.
- Each value is retried up to `--max-retries` times (default 3) with exponential
  backoff of 1 s, 2 s, ...; empty backend responses count as failures.
- `validate` reports remaining Chinese fields and exits with status 1 when a record
  is not a JSON object.

Not yet implemented:

- Refusing to overwrite the original dataset (an output path equal to the input path
  is not detected).
- Logging failed translations and continuing: a value that still fails after all
  retries stops the run; already checkpointed records are kept for resumption.
- Including remaining-Chinese counts in the merge report (run `validate` instead).
- Checking required keys or a full record schema.

## Translation quality

Machine translation can alter technical terminology, code, equations, proper names,
formatting, and safety-sensitive content. A successful API response does not imply
a correct translation. Users should review a statistically meaningful sample and
manually inspect important records before training or evaluation.

For reproducible research, a release should record the translation backend, source
and target languages, execution date, dependency versions, filtering rules, retry
policy, and hashes of input and output files.

## Data provenance and release policy

The current input filename indicates that the data was downloaded from an external
dataset platform, but the exact dataset card and license have not yet been confirmed.
For that reason:

- The full original dataset is not included.
- The full translated dataset is not included.
- Only small synthetic or clearly redistributable examples should be committed.
- A future data release must cite the exact source dataset and comply with its
  license and attribution requirements.

If redistribution is permitted, large generated artifacts are better published as
a versioned dataset release rather than committed repeatedly to Git history.

## Known limitations

- The detector matches CJK Unified Ideographs, Extension A, and Compatibility
  Ideographs (U+3400–4DBF, U+4E00–9FFF, U+F900–FAFF). A single such character marks
  the whole field for translation, so mostly English fields with a short Chinese
  term are translated in full; Japanese kanji are also matched.
- Translation requests are sent sequentially and may be slow for large datasets.
- Only the Google backend (via `deep-translator`) is wired into the CLI.
- Translation-service behavior can change over time.

## Contributing

Contributions are welcome. Especially useful areas include language-detection
tests, backend adapters, failure logging, schema validation, terminology
preservation, and merge-integrity checks.

Do not submit private data, access credentials, or third-party datasets without
clear redistribution permission.

## Citation

A formal citation will be added with the first versioned release. Until then, cite
the repository URL and the exact commit used.

## License

No public license has been selected yet. The code license and any future dataset
license will be documented separately after ownership and source-data obligations
have been confirmed.
