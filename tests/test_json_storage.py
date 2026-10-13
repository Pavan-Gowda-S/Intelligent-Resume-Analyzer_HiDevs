"""Tests for json_storage.py"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.models import (
    AnalysisSession, CandidateAnalysis, JobDescription, ScoreBreakdown,
)


# ── Fixtures — use temp directories so tests are isolated ─────────────────

@pytest.fixture(autouse=True)
def _patch_paths(tmp_path, monkeypatch):
    """Redirect all storage paths to a temporary directory."""
    import src.json_storage as storage
    import src.config as cfg

    monkeypatch.setattr(storage, "JOBS_FILE", tmp_path / "jobs.json")
    monkeypatch.setattr(storage, "CANDIDATES_FILE", tmp_path / "candidates.json")
    monkeypatch.setattr(storage, "SESSIONS_FILE", tmp_path / "sessions.json")
    monkeypatch.setattr(cfg, "JOBS_FILE", tmp_path / "jobs.json")
    monkeypatch.setattr(cfg, "CANDIDATES_FILE", tmp_path / "candidates.json")
    monkeypatch.setattr(cfg, "SESSIONS_FILE", tmp_path / "sessions.json")
    yield


def _make_job(**kwargs) -> JobDescription:
    defaults = {
        "title": "Test Job",
        "description": "A test job",
        "required_skills": ["Python"],
        "preferred_skills": ["Docker"],
    }
    defaults.update(kwargs)
    return JobDescription(**defaults)


def _make_analysis(**kwargs) -> CandidateAnalysis:
    defaults = {
        "job_id": "j1",
        "session_id": "s1",
        "job_title": "Test Job",
        "filename": "resume.txt",
        "candidate_name": "Test Candidate",
    }
    defaults.update(kwargs)
    return CandidateAnalysis(**defaults)


def _make_session(**kwargs) -> AnalysisSession:
    defaults = {
        "job_id": "j1",
        "job_title": "Test Job",
    }
    defaults.update(kwargs)
    return AnalysisSession(**defaults)


# ── Job CRUD ──────────────────────────────────────────────────────────────

def test_save_and_load_job():
    from src.json_storage import save_job, load_jobs
    job = _make_job()
    save_job(job)
    jobs = load_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job.id


def test_get_job_by_id():
    from src.json_storage import save_job, get_job
    job = _make_job()
    save_job(job)
    found = get_job(job.id)
    assert found is not None
    assert found.title == "Test Job"


def test_get_job_missing():
    from src.json_storage import get_job
    assert get_job("nonexistent-id") is None


def test_delete_job():
    from src.json_storage import save_job, delete_job, load_jobs
    job = _make_job()
    save_job(job)
    result = delete_job(job.id)
    assert result is True
    assert len(load_jobs()) == 0


def test_delete_nonexistent_job():
    from src.json_storage import delete_job
    assert delete_job("does-not-exist") is False


def test_save_job_updates_existing():
    from src.json_storage import save_job, load_jobs
    job = _make_job()
    save_job(job)
    job.title = "Updated Title"
    save_job(job)
    jobs = load_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Updated Title"


# ── Candidate CRUD ────────────────────────────────────────────────────────

def test_save_and_load_candidate():
    from src.json_storage import save_candidate_analysis, load_candidate_analyses
    a = _make_analysis()
    save_candidate_analysis(a)
    records = load_candidate_analyses()
    assert len(records) == 1
    assert records[0].id == a.id


def test_get_candidate_analysis():
    from src.json_storage import save_candidate_analysis, get_candidate_analysis
    a = _make_analysis()
    save_candidate_analysis(a)
    found = get_candidate_analysis(a.id)
    assert found is not None
    assert found.candidate_name == "Test Candidate"


def test_delete_candidate_analysis():
    from src.json_storage import save_candidate_analysis, delete_candidate_analysis, load_candidate_analyses
    a = _make_analysis()
    save_candidate_analysis(a)
    delete_candidate_analysis(a.id)
    assert len(load_candidate_analyses()) == 0


def test_get_analyses_for_session():
    from src.json_storage import save_candidate_analysis, get_analyses_for_session
    a1 = _make_analysis(session_id="session-A")
    a2 = _make_analysis(session_id="session-B")
    save_candidate_analysis(a1)
    save_candidate_analysis(a2)
    results = get_analyses_for_session("session-A")
    assert len(results) == 1
    assert results[0].id == a1.id


# ── Sessions ──────────────────────────────────────────────────────────────

def test_save_and_load_session():
    from src.json_storage import save_session, load_sessions
    s = _make_session()
    save_session(s)
    sessions = load_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == s.id


def test_delete_session_also_removes_candidates():
    from src.json_storage import (
        save_session, save_candidate_analysis,
        delete_session, load_candidate_analyses,
    )
    s = _make_session()
    save_session(s)
    a = _make_analysis(session_id=s.id)
    save_candidate_analysis(a)
    delete_session(s.id)
    # Associated candidates should be removed
    remaining = [
        c for c in load_candidate_analyses()
        if c.session_id == s.id
    ]
    assert len(remaining) == 0


# ── Corrupt JSON recovery ─────────────────────────────────────────────────

def test_corrupt_json_returns_empty(tmp_path, monkeypatch):
    import src.json_storage as storage
    corrupt_file = tmp_path / "jobs.json"
    corrupt_file.write_text("NOT VALID JSON {{{{", encoding="utf-8")
    monkeypatch.setattr(storage, "JOBS_FILE", corrupt_file)
    jobs = storage.load_jobs()
    assert jobs == []


# ── Dashboard stats ───────────────────────────────────────────────────────

def test_dashboard_stats_empty():
    from src.json_storage import get_dashboard_stats
    stats = get_dashboard_stats()
    assert stats["total_resumes"] == 0
    assert stats["avg_score"] == 0.0


def test_dashboard_stats_with_data():
    from src.json_storage import save_candidate_analysis, get_dashboard_stats
    a = _make_analysis()
    a.score_breakdown = ScoreBreakdown(total_score=80.0, alignment_label="Strong Alignment")
    save_candidate_analysis(a)
    stats = get_dashboard_stats()
    assert stats["total_resumes"] == 1
    assert stats["avg_score"] == 80.0


# ── Clear data ────────────────────────────────────────────────────────────

def test_clear_all_data():
    from src.json_storage import (
        save_candidate_analysis, save_session, save_job,
        clear_all_data, load_candidate_analyses, load_sessions, load_jobs,
    )
    save_job(_make_job())
    save_session(_make_session())
    save_candidate_analysis(_make_analysis())
    clear_all_data()
    assert len(load_candidate_analyses()) == 0
    assert len(load_sessions()) == 0
    assert len(load_jobs()) == 1  # Jobs should be preserved


def test_clear_all():
    from src.json_storage import (
        save_job, clear_all, load_jobs,
    )
    save_job(_make_job())
    clear_all()
    assert len(load_jobs()) == 0
