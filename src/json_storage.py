"""
JSON-based persistence layer.

All reads and writes go through this module. Files are written atomically
(write to temp file, then rename) where the OS supports it.  No personal
resume content is persisted — only structured analysis results.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import CANDIDATES_FILE, JOBS_FILE, SESSIONS_FILE
from src.models import AnalysisSession, CandidateAnalysis, JobDescription

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level I/O helpers
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, data: Any) -> None:
    """Write *data* as JSON to *path* atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on failure; do not partially overwrite target
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _safe_read(path: Path) -> list[dict]:
    """Read a JSON array from *path*.  Returns [] on missing/corrupt files."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        logger.warning("Expected JSON array in %s; got %s — returning empty list.", path, type(data))
        return []
    except json.JSONDecodeError as exc:
        logger.warning("Corrupt JSON in %s (%s) — returning empty list.", path, exc)
        return []
    except OSError as exc:
        logger.warning("Cannot read %s: %s — returning empty list.", path, exc)
        return []


# ---------------------------------------------------------------------------
# Job descriptions
# ---------------------------------------------------------------------------

def save_job(job: JobDescription) -> None:
    jobs = _safe_read(JOBS_FILE)
    # Replace existing record with same id, or append new one
    updated = False
    for i, j in enumerate(jobs):
        if j.get("id") == job.id:
            jobs[i] = job.to_dict()
            updated = True
            break
    if not updated:
        jobs.append(job.to_dict())
    _atomic_write(JOBS_FILE, jobs)


def load_jobs() -> list[JobDescription]:
    return [JobDescription.from_dict(d) for d in _safe_read(JOBS_FILE)]


def get_job(job_id: str) -> JobDescription | None:
    for d in _safe_read(JOBS_FILE):
        if d.get("id") == job_id:
            return JobDescription.from_dict(d)
    return None


def delete_job(job_id: str) -> bool:
    jobs = _safe_read(JOBS_FILE)
    filtered = [j for j in jobs if j.get("id") != job_id]
    if len(filtered) == len(jobs):
        return False
    _atomic_write(JOBS_FILE, filtered)
    return True


# ---------------------------------------------------------------------------
# Candidate analyses
# ---------------------------------------------------------------------------

def save_candidate_analysis(analysis: CandidateAnalysis) -> None:
    records = _safe_read(CANDIDATES_FILE)
    updated = False
    for i, r in enumerate(records):
        if r.get("id") == analysis.id:
            records[i] = analysis.to_dict()
            updated = True
            break
    if not updated:
        records.append(analysis.to_dict())
    _atomic_write(CANDIDATES_FILE, records)


def load_candidate_analyses() -> list[CandidateAnalysis]:
    return [CandidateAnalysis.from_dict(d) for d in _safe_read(CANDIDATES_FILE)]


def get_candidate_analysis(analysis_id: str) -> CandidateAnalysis | None:
    for d in _safe_read(CANDIDATES_FILE):
        if d.get("id") == analysis_id:
            return CandidateAnalysis.from_dict(d)
    return None


def delete_candidate_analysis(analysis_id: str) -> bool:
    records = _safe_read(CANDIDATES_FILE)
    filtered = [r for r in records if r.get("id") != analysis_id]
    if len(filtered) == len(records):
        return False
    _atomic_write(CANDIDATES_FILE, filtered)
    return True


def get_analyses_for_session(session_id: str) -> list[CandidateAnalysis]:
    return [
        CandidateAnalysis.from_dict(d)
        for d in _safe_read(CANDIDATES_FILE)
        if d.get("session_id") == session_id
    ]


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def save_session(session: AnalysisSession) -> None:
    sessions = _safe_read(SESSIONS_FILE)
    updated = False
    for i, s in enumerate(sessions):
        if s.get("id") == session.id:
            sessions[i] = session.to_dict()
            updated = True
            break
    if not updated:
        sessions.append(session.to_dict())
    _atomic_write(SESSIONS_FILE, sessions)


def load_sessions() -> list[AnalysisSession]:
    return [AnalysisSession.from_dict(d) for d in _safe_read(SESSIONS_FILE)]


def delete_session(session_id: str) -> bool:
    sessions = _safe_read(SESSIONS_FILE)
    filtered = [s for s in sessions if s.get("id") != session_id]
    if len(filtered) == len(sessions):
        return False
    _atomic_write(SESSIONS_FILE, filtered)
    # Also delete associated candidate analyses
    records = _safe_read(CANDIDATES_FILE)
    remaining = [r for r in records if r.get("session_id") != session_id]
    _atomic_write(CANDIDATES_FILE, remaining)
    return True


# ---------------------------------------------------------------------------
# Data-clearing helper
# ---------------------------------------------------------------------------

def clear_all_data() -> None:
    """Delete all stored analysis data. Does NOT delete job descriptions."""
    for path in (SESSIONS_FILE, CANDIDATES_FILE):
        if path.exists():
            _atomic_write(path, [])
    logger.info("All analysis data cleared.")


def clear_all() -> None:
    """Delete ALL stored data including jobs."""
    for path in (JOBS_FILE, SESSIONS_FILE, CANDIDATES_FILE):
        if path.exists():
            _atomic_write(path, [])
    logger.info("All application data cleared.")


# ---------------------------------------------------------------------------
# Dashboard stats helper
# ---------------------------------------------------------------------------

def get_dashboard_stats() -> dict[str, Any]:
    jobs = _safe_read(JOBS_FILE)
    sessions = _safe_read(SESSIONS_FILE)
    candidates = _safe_read(CANDIDATES_FILE)

    scores = [
        c["score_breakdown"]["total_score"]
        for c in candidates
        if "score_breakdown" in c and "total_score" in c["score_breakdown"]
    ]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    needs_review = sum(
        1 for c in candidates
        if c.get("score_breakdown", {}).get("alignment_label") == "Needs Manual Review"
    )

    return {
        "total_resumes": len(candidates),
        "total_jobs": len(jobs),
        "total_sessions": len(sessions),
        "avg_score": avg_score,
        "needs_manual_review": needs_review,
        "score_distribution": scores,
        "recent_sessions": sorted(sessions, key=lambda s: s.get("created_at", ""), reverse=True)[:5],
    }
