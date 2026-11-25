# Cross-league translation for European basketball: companion repository

Companion to the SSAC 2027 research paper *"European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To"* (Amir Tahori, Submission 47).
This repository: https://github.com/AT020993/cross-league-translation.

## Three sections

| Folder | What it is | Check it |
|---|---|---|
| `ssac27-fullpaper/` | **The full paper** (November 2026): manuscript, figures, pre-registration and amendments, results, code, and the derived tables the results are recomputed from | `python reproduce.py --section fullpaper` |
| `ssac27-v10/` | The submitted abstract (29 September 2026), unchanged | `python reproduce.py --section v10` |
| top level (`scripts/`, `src/`, `data/`, `docs/`, `formal/`) | The September 2026 research companion the abstract grew from, unchanged | `python reproduce.py --section historical` |

`python reproduce.py` runs all three. Start with `ssac27-fullpaper/README.md`.

The top-level folders are the 6 September 2026 cut, kept byte for byte (its own `reproduce.py` is
now `reproduce_historical.py`). Their notes describe earlier drafts, including a 17.6% holdout
figure and an NBA arm that are **not** results of the full paper; read them as history.

## Setup

Python 3.13 and the pinned packages, in a fresh environment:

```sh
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py
```

Reproduction makes no network requests. Allow about ten minutes on a recent laptop; most of it is
the full paper (measured runs are in `ssac27-fullpaper/README.md`). The run ends with a summary:
one line per section, each `passed` or `FAILED`. `python -m pytest -q` runs the tests of the
September 2026 companion under `tests/`; it is optional.

## Provenance

This cut was made from the private research repository at commit `d4ce6f536aa9e6b6fa3986f123f596b6fa1d6985` by
`scripts/export_public_translation_repo.py --fullpaper-cut`. The historical and v10 files are carried
from public commit `fc89c2049` and checked file by file against their git hashes.
`MANIFEST.json` lists the sha256 of every file. The release is one commit on top of the public
history, with a tag; earlier public commits are not rewritten. `REGISTRATION_HASHES.md` fixes the
content of the pre-registration, its amendments and the frozen forecast files by sha256.

## Data terms and licence

See `DATA_TERMS.md` (sources, credit and scope) and `LICENSING.md` (MIT for the code; see `LICENSE`).
