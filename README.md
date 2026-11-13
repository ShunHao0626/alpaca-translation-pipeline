# Alpaca Translation Pipeline

**English** · [简体中文](README_CN.md)

Alpaca Translation Pipeline is a reproducible workflow for identifying,
cleaning, translating, and reintegrating Chinese text in Alpaca-style instruction
datasets. It was created from an earlier one-off data-cleaning project and is being
refactored into a small command-line tool with tests and explicit provenance.

The repository is intended to contain processing code and small examples. The
original and translated full datasets will not be redistributed until their source
license and publication rights have been verified.

## Project status

The historical pipeline successfully produced a translated working copy. This
repository consolidates that work into an installable command-line tool with atomic
JSON writes, resumable translation output, merge-integrity reports, and tests.

| Stage | Historical implementation | Planned release |
| --- | --- | --- |
| Chinese-text detection | Available | Consolidated and tested |
| Candidate cleanup | Available | Alignment-safe cleanup |
| Translation and retry handling | Available | Resumable execution |
| Merge into original dataset | Available | Validated merge report |
| Command-line interface | Available | Five subcommands |
| Automated tests | Included | No network required |

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
Remove empty and non-Chinese candidate fields
      |
      v
Translate instruction/output fields with retries
      |
      v
Merge translated records into a copy of the original dataset
      |
      v
Validate record count, keys, and remaining Chinese text
```

Every stage writes a new artifact. The original input should remain immutable.

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

The cleanup will also support selecting which string fields are translated rather
than assuming that only `instruction` and `output` are relevant.

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
│   ├── detect.py
│   ├── clean.py
│   ├── translate.py
│   ├── merge.py
│   ├── validate.py
│   └── cli.py
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
git clone <repository-url>
cd alpaca-translation-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[google]'
```

The `google` extra installs `deep-translator`. Detection, cleanup, merge, validation,
and the test suite do not require network access or a translation dependency.

## Command-line interface

```bash
# Find records containing Chinese text.
python -m alpaca_translation detect \
  --input dataset.json \
  --output work/candidates.json

# Remove duplicate paths and unsuitable candidates.
python -m alpaca_translation clean \
  --input work/candidates.json \
  --output work/candidates-cleaned.json

# Translate selected fields. Progress should be resumable.
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
```

## Safety and validation rules

The cleaned implementation should enforce the following rules:

- Never overwrite the original dataset by default.
- Preserve record order and total record count during merging.
- Preserve fields that were not selected for translation.
- Save progress so interrupted translation jobs can resume.
- Retry transient translation failures with bounded exponential backoff.
- Record failed and unchanged translations without logging secrets.
- Report remaining Chinese text after the merge.
- Validate JSON syntax and the expected schema at every stage.

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

- The current detector focuses on the basic CJK Unified Ideographs range.
- English-dominance heuristics can misclassify mixed-language technical text.
- The historical translator creates network requests sequentially and may be slow.
- Translation-service behavior can change over time.
- The old scripts use fixed filenames and, in one case, an obsolete Windows path.
- The historical log is large and should not be committed.

## Contributing

Contributions are welcome after the first packaged release. Especially useful areas
include language-detection tests, resumable translation, backend adapters, schema
validation, terminology preservation, and merge-integrity checks.

Do not submit private data, access credentials, or third-party datasets without
clear redistribution permission.

## Citation

A formal citation will be added with the first versioned release. Until then, cite
the repository URL and the exact commit used.

## License

No public license has been selected yet. The code license and any future dataset
license will be documented separately after ownership and source-data obligations
have been confirmed.
