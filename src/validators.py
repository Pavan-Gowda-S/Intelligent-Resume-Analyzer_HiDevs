"""
Input validation helpers.

All validation functions return a tuple (is_valid: bool, message: str).
"""

from __future__ import annotations

import os
from pathlib import Path

from src.config import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS


def validate_file_extension(filename: str) -> tuple[bool, str]:
    """Check that the file has an allowed extension."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, (
            f"File '{filename}' has unsupported extension '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}."
        )
    return True, ""


def validate_file_size(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """Ensure the file does not exceed the configured size limit."""
    size = len(file_bytes)
    if size == 0:
        return False, f"File '{filename}' is empty."
    if size > MAX_FILE_SIZE_BYTES:
        mb = size / (1024 * 1024)
        return False, (
            f"File '{filename}' is {mb:.1f} MB, which exceeds the "
            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit."
        )
    return True, ""


def validate_job_title(title: str) -> tuple[bool, str]:
    title = title.strip()
    if not title:
        return False, "Job title cannot be empty."
    if len(title) > 200:
        return False, "Job title must be 200 characters or fewer."
    return True, ""


def validate_job_description(description: str) -> tuple[bool, str]:
    description = description.strip()
    if not description:
        return False, "Job description cannot be empty."
    if len(description) < 20:
        return False, "Job description is too short (minimum 20 characters)."
    return True, ""


def validate_skills_list(skills: list[str]) -> tuple[bool, str]:
    """Ensure skill entries are strings and non-empty."""
    for s in skills:
        if not isinstance(s, str):
            return False, f"Skills must be strings, got: {type(s).__name__}."
        if len(s.strip()) == 0:
            return False, "Skill entries must not be blank."
    return True, ""


def validate_experience_years(value: float | None) -> tuple[bool, str]:
    if value is None:
        return True, ""
    if not isinstance(value, (int, float)):
        return False, "Experience years must be a number."
    if value < 0 or value > 60:
        return False, "Experience years must be between 0 and 60."
    return True, ""


def validate_candidate_analysis_dict(d: dict) -> tuple[bool, str]:
    required_keys = {"id", "job_id", "resume_id", "analyzed_at"}
    missing = required_keys - set(d.keys())
    if missing:
        return False, f"Candidate analysis record missing keys: {missing}."
    return True, ""


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe version of *name*."""
    import re
    safe = re.sub(r"[^\w\-_\. ]", "_", name)
    safe = safe.strip(". ")
    return safe[:100] or "file"
