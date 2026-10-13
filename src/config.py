"""
Application-wide configuration and constants.

All tunable values live here so they can be changed without touching
business-logic modules.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
REPORTS_DIR: Path = BASE_DIR / "reports"
SAMPLE_DATA_DIR: Path = BASE_DIR / "sample_data"

# Ensure runtime directories exist
for _d in (DATA_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Storage file paths
# ---------------------------------------------------------------------------

JOBS_FILE: Path = DATA_DIR / "jobs.json"
SESSIONS_FILE: Path = DATA_DIR / "sessions.json"
CANDIDATES_FILE: Path = DATA_DIR / "candidates.json"

# ---------------------------------------------------------------------------
# Upload constraints
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".txt")
MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

# ---------------------------------------------------------------------------
# Matching-score weights (must sum to 100)
# ---------------------------------------------------------------------------

WEIGHT_REQUIRED_SKILLS: int = 50
WEIGHT_PREFERRED_SKILLS: int = 20
WEIGHT_EXPERIENCE: int = 20
WEIGHT_KEYWORDS: int = 10

assert (
    WEIGHT_REQUIRED_SKILLS
    + WEIGHT_PREFERRED_SKILLS
    + WEIGHT_EXPERIENCE
    + WEIGHT_KEYWORDS
    == 100
), "Score weights must sum to 100."

# ---------------------------------------------------------------------------
# Score-label thresholds (lower bound inclusive)
# ---------------------------------------------------------------------------

LABEL_STRONG: int = 75       # Strong alignment
LABEL_MODERATE: int = 50     # Moderate alignment
LABEL_LIMITED: int = 25      # Limited alignment
# Below LABEL_LIMITED → "Needs Manual Review"

# ---------------------------------------------------------------------------
# Experience handling
# ---------------------------------------------------------------------------

# When experience cannot be determined, award this fraction of the
# experience component (0.0 = penalise fully, 0.5 = neutral).
UNKNOWN_EXPERIENCE_FRACTION: float = 0.5

# ---------------------------------------------------------------------------
# Report settings
# ---------------------------------------------------------------------------

REPORT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
