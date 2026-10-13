"""Tests for matching_engine.py"""

from __future__ import annotations

import pytest
from src.matching_engine import score_candidate, _experience_fraction, _label
from src.models import JobDescription, ParsedResume, ScoreBreakdown
from src.config import (
    WEIGHT_REQUIRED_SKILLS, WEIGHT_PREFERRED_SKILLS,
    WEIGHT_EXPERIENCE, WEIGHT_KEYWORDS,
    UNKNOWN_EXPERIENCE_FRACTION,
    LABEL_STRONG, LABEL_MODERATE, LABEL_LIMITED,
)


def _make_job(
    required: list[str] | None = None,
    preferred: list[str] | None = None,
    min_exp: float | None = None,
    keywords: list[str] | None = None,
) -> JobDescription:
    return JobDescription(
        title="Test Job",
        description="Test description",
        required_skills=required or [],
        preferred_skills=preferred or [],
        min_experience_years=min_exp,
        keywords=keywords or [],
    )


def _make_resume(
    skills: list[str] | None = None,
    exp_months: int | None = None,
    raw_text: str = "",
) -> ParsedResume:
    return ParsedResume(
        filename="test.txt",
        skills=skills or [],
        total_experience_months=exp_months,
        raw_text=raw_text,
    )


# ── Score range ────────────────────────────────────────────────────────────

def test_score_is_between_0_and_100():
    job = _make_job(required=["Python", "FastAPI"], min_exp=3.0)
    resume = _make_resume(skills=["Python"], exp_months=24)
    bd = score_candidate(resume, job)
    assert 0 <= bd.total_score <= 100


def test_perfect_match_score_near_max():
    """Candidate matching all required + preferred skills should score high."""
    job = _make_job(
        required=["Python", "FastAPI"],
        preferred=["Docker"],
        min_exp=2.0,
    )
    resume = _make_resume(
        skills=["Python", "FastAPI", "Docker"],
        exp_months=36,
        raw_text="Python FastAPI Docker REST APIs",
    )
    bd = score_candidate(resume, job)
    assert bd.total_score >= 70


def test_zero_match_score_low():
    """No skill overlap, no experience → low score (but not 0, since no preferred
    skills and no keyword overlap award baseline points by design)."""
    job = _make_job(required=["Python", "FastAPI", "Docker"], min_exp=5.0)
    resume = _make_resume(skills=[], exp_months=0)
    bd = score_candidate(resume, job)
    # Required = 0/50, Experience = 0/20 → at most 30 pts (preferred + keywords baseline)
    assert bd.total_score <= 35
    assert bd.required_skills_score == 0.0


def test_no_required_skills_awards_full_component():
    """When job specifies no required skills, component gives full marks."""
    job = _make_job(required=[], preferred=[], min_exp=None)
    resume = _make_resume(skills=[], exp_months=None)
    bd = score_candidate(resume, job)
    assert bd.required_skills_score == WEIGHT_REQUIRED_SKILLS


def test_no_preferred_skills_awards_full_component():
    job = _make_job(required=["Python"], preferred=[])
    resume = _make_resume(skills=["Python"], exp_months=12)
    bd = score_candidate(resume, job)
    assert bd.preferred_skills_score == WEIGHT_PREFERRED_SKILLS


def test_unknown_experience_awards_partial():
    job = _make_job(min_exp=3.0)
    resume = _make_resume(exp_months=None)  # Unknown
    bd = score_candidate(resume, job)
    expected = round(UNKNOWN_EXPERIENCE_FRACTION * WEIGHT_EXPERIENCE, 2)
    assert bd.experience_score == expected
    assert bd.experience_unknown is True


def test_matched_required_correct():
    job = _make_job(required=["Python", "FastAPI", "Docker"])
    resume = _make_resume(skills=["Python", "FastAPI"])
    bd = score_candidate(resume, job)
    matched_lower = [s.lower() for s in bd.matched_required]
    assert "python" in matched_lower
    assert "fastapi" in matched_lower
    assert len(bd.missing_required) == 1
    assert bd.missing_required[0].lower() == "docker"


def test_missing_required_correct():
    job = _make_job(required=["Python", "Go", "Rust"])
    resume = _make_resume(skills=["Python"])
    bd = score_candidate(resume, job)
    assert len(bd.missing_required) == 2


def test_preferred_skills_matched():
    job = _make_job(preferred=["AWS", "Kubernetes"])
    resume = _make_resume(skills=["AWS"])
    bd = score_candidate(resume, job)
    assert len(bd.matched_preferred) == 1
    assert "AWS" in bd.matched_preferred


def test_experience_fraction_sufficient():
    """Candidate with enough experience should get full experience component."""
    fraction, yrs, unknown = _experience_fraction(3.0, 48)  # 48 months = 4 yrs ≥ 3 yrs
    assert fraction == 1.0
    assert unknown is False
    assert yrs == 4.0


def test_experience_fraction_partial():
    fraction, yrs, unknown = _experience_fraction(4.0, 24)  # 24 months = 2 yrs vs 4 required
    assert 0 < fraction < 1
    assert unknown is False


def test_experience_fraction_unknown():
    fraction, yrs, unknown = _experience_fraction(3.0, None)
    assert fraction == UNKNOWN_EXPERIENCE_FRACTION
    assert unknown is True
    assert yrs is None


def test_experience_fraction_no_requirement():
    fraction, yrs, unknown = _experience_fraction(None, 24)
    assert fraction == 1.0
    assert unknown is False


def test_label_strong():
    assert _label(LABEL_STRONG) == "Strong Alignment"
    assert _label(100) == "Strong Alignment"


def test_label_moderate():
    assert _label(LABEL_MODERATE) == "Moderate Alignment"


def test_label_limited():
    assert _label(LABEL_LIMITED) == "Limited Alignment"


def test_label_review():
    assert _label(LABEL_LIMITED - 1) == "Needs Manual Review"
    assert _label(0) == "Needs Manual Review"


def test_explanation_not_empty():
    job = _make_job(required=["Python"])
    resume = _make_resume(skills=["Python"], exp_months=24)
    bd = score_candidate(resume, job)
    assert len(bd.explanation) > 50


def test_alignment_label_in_breakdown():
    job = _make_job(required=["Python"])
    resume = _make_resume(skills=["Python"], exp_months=36)
    bd = score_candidate(resume, job)
    assert bd.alignment_label in {
        "Strong Alignment", "Moderate Alignment",
        "Limited Alignment", "Needs Manual Review",
    }


def test_score_deterministic():
    """Same inputs must always produce the same score."""
    job = _make_job(required=["Python", "Docker"], min_exp=3.0)
    resume = _make_resume(skills=["Python"], exp_months=24)
    bd1 = score_candidate(resume, job)
    bd2 = score_candidate(resume, job)
    assert bd1.total_score == bd2.total_score


def test_skill_comparison_case_insensitive():
    """Job skill 'python' should match resume skill 'Python'."""
    job = _make_job(required=["python"])
    resume = _make_resume(skills=["Python"])
    bd = score_candidate(resume, job)
    assert len(bd.matched_required) == 1
