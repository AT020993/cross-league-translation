"""CWD-independent project data locations, resolved once at import.

ISOCOURT_DATA_ROOT may be absolute or relative to this checkout, never the CWD.
Explicit caller paths take precedence over these defaults. This module imports
only the standard library and does not inspect or create any data files.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_override = os.environ.get("ISOCOURT_DATA_ROOT")
DATA_ROOT = Path(_override).expanduser() if _override else PROJECT_ROOT / "data"
if not DATA_ROOT.is_absolute():
    DATA_ROOT = PROJECT_ROOT / DATA_ROOT

RAW_ROOT = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
REGISTRIES_DIR = DATA_ROOT / "registries"
TEAM_ALIASES = REGISTRIES_DIR / "team_aliases.parquet"
QUARTER_SCORES_DERIVED = PROCESSED_DIR / "quarter_scores_derived.parquet"
AUTH_DB = DATA_ROOT / "auth" / "auth.duckdb"
CONVERSATIONS_DB = DATA_ROOT / "conversations" / "conversations.duckdb"
RECORDS_DIR = PROCESSED_DIR / "records"
