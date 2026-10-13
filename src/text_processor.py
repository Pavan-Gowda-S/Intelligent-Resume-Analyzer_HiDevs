"""
Text processing utilities for resume content.

Provides section detection, name/email/phone extraction, and
general cleanup functions used by the resume parser.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Contact extraction
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

_PHONE_RE = re.compile(
    r"(?<!\d)"
    r"(\+?1?\s*[-.]?\s*)?"         # optional country code
    r"(\(?\d{3}\)?[\s.\-]?)"       # area code
    r"(\d{3}[\s.\-]?)"             # prefix
    r"(\d{4})"                     # line number
    r"(?!\d)"
)

# Section headings typically found in resumes
_SECTION_KEYWORDS: dict[str, list[str]] = {
    "contact": ["contact", "personal information", "personal details", "contact information"],
    "summary": ["summary", "profile", "objective", "about me", "professional summary"],
    "skills": [
        "skills", "technical skills", "core competencies", "competencies",
        "technologies", "tech stack", "tools", "proficiencies",
    ],
    "experience": [
        "experience", "work experience", "professional experience", "employment",
        "employment history", "work history", "career history",
    ],
    "education": ["education", "academic background", "academics", "qualifications"],
    "certifications": [
        "certifications", "certificates", "licenses", "accreditations",
        "credentials", "professional development",
    ],
    "projects": ["projects", "personal projects", "key projects"],
    "publications": ["publications", "research", "papers"],
}

# Words that commonly appear at the top of resumes but are NOT names
_NON_NAME_TOKENS: frozenset[str] = frozenset({
    "resume", "curriculum", "vitae", "cv", "profile", "summary",
    "contact", "address", "phone", "email", "objective", "skills",
    "experience", "education", "certifications", "page", "references",
    "linkedin", "github", "twitter", "portfolio", "website", "www",
    "http", "https", "dear", "hiring", "manager", "recruiter",
})

# Regex for a plausible human name: 2-4 words, each Title-cased, 2-25 chars
_NAME_RE = re.compile(
    r"^([A-Z][a-z]{1,24})"        # First name
    r"(?:\s+[A-Z][a-z]{0,4}\.?)?" # Optional middle name/initial
    r"\s+([A-Z][a-z]{1,24})$"     # Last name
)


def extract_email(text: str) -> str:
    """Return the first email address found, or empty string."""
    m = _EMAIL_RE.search(text)
    return m.group(0).lower() if m else ""


def extract_phone(text: str) -> str:
    """Return the first plausible phone number found, or empty string."""
    m = _PHONE_RE.search(text)
    if m:
        raw = m.group(0)
        digits = re.sub(r"\D", "", raw)
        if len(digits) >= 10:
            return raw.strip()
    return ""


def extract_candidate_name(
    text: str,
    filename: str = "",
) -> tuple[str, str]:
    """
    Attempt to extract a candidate name from the top of the resume text.

    Returns (name, confidence) where confidence ∈ {"high", "medium", "low", "unknown"}.

    Strategy:
    1. Check the first 10 non-empty lines for a plausible name pattern.
    2. Reject tokens that match known non-name keywords.
    3. Do NOT use the email address, phone, or filename as the name.
    """
    email = extract_email(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:20]

    for line in lines:
        # Skip lines that look like emails, URLs, or section headings
        if "@" in line or line.lower().startswith("http"):
            continue
        tokens = line.lower().split()
        if any(t in _NON_NAME_TOKENS for t in tokens):
            continue
        # Remove punctuation except hyphens for name check
        clean = re.sub(r"[^\w\s\-\.]", "", line).strip()
        if not clean:
            continue
        m = _NAME_RE.match(clean)
        if m:
            return line.strip(), "high"

    # Fallback: try to find any Title Case bigram that is not an email
    for line in lines[:10]:
        if "@" in line or re.search(r"\d{5,}", line):
            continue
        words = line.split()
        if len(words) == 2:
            w0, w1 = words
            if (
                w0[0].isupper() and w1[0].isupper()
                and len(w0) > 1 and len(w1) > 1
                and w0.lower() not in _NON_NAME_TOKENS
                and w1.lower() not in _NON_NAME_TOKENS
            ):
                return line.strip(), "medium"

    return "", "unknown"


# ---------------------------------------------------------------------------
# Section segmentation
# ---------------------------------------------------------------------------

def _is_section_header(line: str, section_keys: list[str]) -> bool:
    """Return True if *line* looks like a section header for the given keys."""
    ln = re.sub(r"[^\w\s]", "", line).strip().lower()
    return ln in section_keys or any(k in ln for k in section_keys)


def segment_sections(text: str) -> dict[str, str]:
    """
    Split resume text into named sections.

    Returns a dict mapping section name to the raw text of that section.
    An 'other' key collects text before any recognised section header.
    """
    lines = text.splitlines()
    sections: dict[str, list[str]] = {"other": []}
    current_section = "other"

    for line in lines:
        matched_section: str | None = None
        for section, keywords in _SECTION_KEYWORDS.items():
            if _is_section_header(line, keywords):
                matched_section = section
                break
        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


# ---------------------------------------------------------------------------
# Education extraction
# ---------------------------------------------------------------------------

_DEGREE_KEYWORDS = [
    "bachelor", "b.s.", "b.sc", "b.tech", "b.e.", "b.a.",
    "master", "m.s.", "m.sc", "m.tech", "m.e.", "m.a.", "mba",
    "ph.d", "phd", "doctor",
    "associate", "diploma", "high school", "secondary",
    "b.com", "m.com", "b.ca", "mca",
]

_INSTITUTION_KEYWORDS = [
    "university", "college", "institute", "school", "academy",
    "polytechnic", "iit", "nit", "bits",
]


def extract_education_entries(text: str) -> list[dict[str, str]]:
    """
    Parse education section text and return a list of raw education entry dicts.
    """
    entries: list[dict[str, str]] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for i, line in enumerate(lines):
        ll = line.lower()
        has_degree = any(kw in ll for kw in _DEGREE_KEYWORDS)
        has_inst = any(kw in ll for kw in _INSTITUTION_KEYWORDS)
        if has_degree or has_inst:
            year_m = re.search(r"\b(19[6-9]\d|20[0-4]\d)\b", line)
            entries.append({
                "degree": line if has_degree else "",
                "institution": line if has_inst else "",
                "year": year_m.group(1) if year_m else "",
                "raw_text": line,
            })

    return entries


# ---------------------------------------------------------------------------
# Experience extraction
# ---------------------------------------------------------------------------

_DATE_RANGE_RE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(19[6-9]\d|20[0-4]\d)"
    r"\s*[-–—to]+\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(19[6-9]\d|20[0-4]\d|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)",
    re.IGNORECASE,
)


def extract_experience_entries(text: str) -> list[dict]:
    """
    Heuristically extract work experience entries from experience section text.
    Returns list of dicts with keys: title, employer, start_date, end_date,
    raw_text.
    """
    entries: list[dict] = []
    blocks = re.split(r"\n{2,}", text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        date_m = _DATE_RANGE_RE.search(block)
        entry: dict = {
            "title": "",
            "employer": "",
            "start_date": "",
            "end_date": "",
            "responsibilities": [],
            "raw_text": block,
        }
        if date_m:
            s_month = date_m.group(1) or ""
            s_year = date_m.group(2) or ""
            e_month = date_m.group(3) or ""
            e_year = date_m.group(4) or ""
            entry["start_date"] = f"{s_month}{s_year}".strip()
            entry["end_date"] = f"{e_month}{e_year}".strip()

        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines:
            entry["title"] = lines[0]
        if len(lines) > 1:
            entry["employer"] = lines[1]
        if len(lines) > 2:
            entry["responsibilities"] = lines[2:]

        entries.append(entry)

    return entries


# ---------------------------------------------------------------------------
# Certification extraction
# ---------------------------------------------------------------------------

_CERT_KEYWORDS = [
    "certified", "certification", "certificate", "aws certified",
    "google certified", "microsoft certified", "comptia",
    "pmp", "cpa", "cfa", "cissp", "cism", "ccna", "ccnp",
    "oracle certified", "red hat", "rhce", "scrum master",
]


def extract_certifications(text: str) -> list[str]:
    """Return lines that appear to describe certifications."""
    results: list[str] = []
    for line in text.splitlines():
        ll = line.lower()
        if any(kw in ll for kw in _CERT_KEYWORDS):
            clean = line.strip()
            if clean and clean not in results:
                results.append(clean)
    return results


# ---------------------------------------------------------------------------
# Experience year estimation
# ---------------------------------------------------------------------------

def estimate_total_experience_months(entries: list[dict]) -> int | None:
    """
    Sum up durations from extracted work experience entries.

    Returns total months or None if dates are too ambiguous.
    """
    from src.utils import months_between
    total = 0
    found_any = False

    for e in entries:
        start = e.get("start_date", "")
        end = e.get("end_date", "")
        if not start:
            continue
        months = months_between(start, end or "present")
        if months is not None:
            total += months
            found_any = True

    return total if found_any else None
