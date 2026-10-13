"""
Job description analyzer.

Converts free-text job descriptions into structured JobDescription objects.
Skill extraction from JDs uses the same taxonomy as resume parsing.
"""

from __future__ import annotations

import re

from src.models import JobDescription
from src.skill_extractor import extract_skills
from src.utils import normalize_text, extract_sentences

# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "will", "would",
    "shall", "should", "may", "might", "can", "could", "do", "does",
    "did", "not", "we", "you", "they", "our", "your", "their",
    "this", "that", "these", "those", "as", "it", "its", "also",
    "must", "need", "required", "ability", "experience", "work",
    "team", "strong", "good", "excellent", "excellent", "plus",
    "preferred", "knowledge", "understanding", "familiarity",
    "background", "candidate", "position", "role", "job", "function",
    "including", "such", "well", "highly", "very", "more", "than",
    "across", "within", "using", "through", "up", "out", "if",
    "year", "years", "month", "months",
})


def _extract_keywords(text: str, max_kw: int = 30) -> list[str]:
    """Extract meaningful keywords from text, excluding stopwords and short tokens."""
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-\.#\+]{2,}\b", text)
    seen: dict[str, int] = {}
    for tok in tokens:
        lower = tok.lower()
        if lower not in _STOPWORDS:
            seen[lower] = seen.get(lower, 0) + 1
    # Return top tokens by frequency, title-cased
    ranked = sorted(seen.items(), key=lambda x: -x[1])[:max_kw]
    return [tok.capitalize() for tok, _ in ranked]


# ---------------------------------------------------------------------------
# Responsibility extraction
# ---------------------------------------------------------------------------

_RESPONSIBILITY_STARTERS = re.compile(
    r"(?:^|\n)\s*[\-\*\•\·]\s*(.+)",
    re.MULTILINE,
)


def _extract_responsibilities(text: str) -> list[str]:
    """Pull out bullet-pointed responsibility lines."""
    bullets = _RESPONSIBILITY_STARTERS.findall(text)
    results: list[str] = []
    for b in bullets:
        clean = b.strip()
        if len(clean) > 15:   # ignore very short / junk bullets
            results.append(clean)
    return results[:20]      # cap at 20


# ---------------------------------------------------------------------------
# Experience requirement extraction
# ---------------------------------------------------------------------------

_EXP_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to\s*\d+\s*)?"
    r"years?(?:\s+of(?:\s+\w+){0,3}?)?\s*experience",
    re.IGNORECASE,
)


def extract_min_experience(text: str) -> float | None:
    """
    Return the minimum years of experience mentioned, or None.
    When a range like '3-5 years' is present, returns the lower bound.
    """
    matches = _EXP_RE.findall(text)
    if matches:
        return float(matches[0])
    return None


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

def analyze_job_description(
    title: str,
    description: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    min_experience_years: float | None = None,
) -> JobDescription:
    """
    Build a structured JobDescription from raw text plus optional overrides.

    The recruiter-supplied required/preferred skill lists always take precedence
    over automatically extracted skills.  Automatic extraction is used only as
    a fallback when those lists are absent.

    Parameters
    ----------
    title : str
        Job title (user-supplied).
    description : str
        Raw job description text.
    required_skills : list[str] | None
        Explicit required skills; skips auto-extraction if provided.
    preferred_skills : list[str] | None
        Explicit preferred skills; skips auto-extraction if provided.
    min_experience_years : float | None
        Explicit minimum experience; auto-extracted if None.
    """
    desc_norm = normalize_text(description)

    # Track whether required/preferred were explicitly provided
    required_explicit = required_skills is not None
    preferred_explicit = preferred_skills is not None

    # Skill extraction
    if required_skills is None:
        # Automatically extract all skills from the description
        auto_skills = extract_skills(desc_norm)
        required_skills = auto_skills  # treat all auto-extracted as required
    if preferred_skills is None:
        preferred_skills = []

    # Normalise and deduplicate (preserve casing from taxonomy)
    def _dedup(lst: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for s in lst:
            key = s.strip().lower()
            if key and key not in seen:
                seen[key] = s.strip()
        return list(seen.values())

    required_skills = _dedup(required_skills)
    preferred_skills = _dedup(preferred_skills)

    # Only remove skills from preferred when BOTH lists were explicitly provided.
    # When required_skills were auto-extracted, preferred is kept as-is.
    if required_explicit and preferred_explicit:
        req_lower = {s.lower() for s in required_skills}
        preferred_skills = [s for s in preferred_skills if s.lower() not in req_lower]

    # Experience
    if min_experience_years is None:
        min_experience_years = extract_min_experience(desc_norm)

    # Responsibilities
    responsibilities = _extract_responsibilities(description)

    # Keywords
    keywords = _extract_keywords(desc_norm)

    return JobDescription(
        title=title.strip(),
        description=description.strip(),
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=min_experience_years,
        responsibilities=responsibilities,
        keywords=keywords,
    )
