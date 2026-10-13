"""
General-purpose utility functions.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime
from typing import Any

from src.config import LOG_LEVEL, REPORT_DATE_FORMAT

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.WARNING))
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize unicode, collapse whitespace, strip control characters."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def normalize_whitespace(text: str) -> str:
    """Collapse all runs of whitespace to a single space."""
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    """Return lowercase word tokens, stripping punctuation."""
    return re.findall(r"\b[a-z][a-z0-9\-]*\b", text.lower())


def extract_sentences(text: str) -> list[str]:
    """Split text into rough sentences."""
    return [s.strip() for s in re.split(r"[.!?;]\s+", text) if s.strip()]


# ---------------------------------------------------------------------------
# Date utilities
# ---------------------------------------------------------------------------

def now_formatted() -> str:
    return datetime.now().strftime(REPORT_DATE_FORMAT)


def parse_year(text: str) -> int | None:
    """Extract a 4-digit year from text, or return None."""
    m = re.search(r"\b(19[6-9]\d|20[0-4]\d)\b", text)
    return int(m.group(1)) if m else None


def months_between(start: str, end: str | None) -> int | None:
    """
    Try to parse 'start' and 'end' (e.g. 'Jan 2020', '2020', 'Present') and
    return the approximate number of months between them.  Returns None on
    failure.
    """
    from dateutil import parser as dparser

    end_text = end or "present"
    if "present" in end_text.lower() or "current" in end_text.lower():
        end_dt = datetime.now()
    else:
        try:
            end_dt = dparser.parse(end_text, default=datetime(datetime.now().year, 12, 1))
        except Exception:
            return None
    try:
        start_dt = dparser.parse(start, default=datetime(2000, 1, 1))
    except Exception:
        return None

    diff = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    return max(0, diff)


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def truncate(text: str, max_len: int = 80, suffix: str = "…") -> str:
    return text if len(text) <= max_len else text[: max_len - len(suffix)] + suffix


def title_case(text: str) -> str:
    return text.strip().title()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def pct(numerator: int, denominator: int) -> float:
    """Return percentage (0-100), or 0 if denominator is 0."""
    return (numerator / denominator * 100) if denominator > 0 else 0.0
