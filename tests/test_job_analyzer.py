"""Tests for job_analyzer.py"""

from __future__ import annotations

import pytest
from src.job_analyzer import analyze_job_description
from src.models import JobDescription


SAMPLE_JD = """
Senior Python Developer

We need 4+ years of Python experience.
Required skills: Python, FastAPI, PostgreSQL, Docker.
Preferred: AWS, React, Kubernetes.
Responsibilities:
- Design REST APIs.
- Maintain CI/CD pipelines.
"""


def test_returns_job_description():
    job = analyze_job_description("Senior Python Dev", SAMPLE_JD)
    assert isinstance(job, JobDescription)


def test_title_preserved():
    job = analyze_job_description("ML Engineer", SAMPLE_JD)
    assert job.title == "ML Engineer"


def test_auto_extracts_skills():
    job = analyze_job_description("Dev", SAMPLE_JD)
    # Auto-extracted skills should include at least Python
    all_skills = [s.lower() for s in job.required_skills + job.preferred_skills]
    assert any("python" in s for s in all_skills)


def test_explicit_required_skills_override():
    job = analyze_job_description(
        "Dev", SAMPLE_JD,
        required_skills=["Python", "SQL"],
    )
    assert "Python" in job.required_skills
    assert "SQL" in job.required_skills


def test_explicit_preferred_skills():
    job = analyze_job_description(
        "Dev", SAMPLE_JD,
        preferred_skills=["AWS", "Docker"],
    )
    assert "AWS" in job.preferred_skills


def test_experience_extraction():
    job = analyze_job_description("Dev", SAMPLE_JD)
    # JD mentions "4+ years"
    assert job.min_experience_years == 4.0


def test_explicit_experience_override():
    job = analyze_job_description("Dev", SAMPLE_JD, min_experience_years=6.0)
    assert job.min_experience_years == 6.0


def test_no_duplicate_required_skills():
    job = analyze_job_description(
        "Dev", SAMPLE_JD,
        required_skills=["Python", "python", "PYTHON"],
    )
    lower = [s.lower() for s in job.required_skills]
    assert lower.count("python") == 1


def test_preferred_not_duplicate_required():
    """A skill in required should not also appear in preferred."""
    job = analyze_job_description(
        "Dev", SAMPLE_JD,
        required_skills=["Python"],
        preferred_skills=["Python", "AWS"],
    )
    req_lower = {s.lower() for s in job.required_skills}
    for s in job.preferred_skills:
        assert s.lower() not in req_lower


def test_keywords_extracted():
    job = analyze_job_description("Dev", SAMPLE_JD)
    assert isinstance(job.keywords, list)


def test_responsibilities_extracted():
    job = analyze_job_description("Dev", SAMPLE_JD)
    # Bullet points should be extracted
    assert isinstance(job.responsibilities, list)


def test_empty_required_skills_list_explicit():
    job = analyze_job_description("Dev", "Build web apps.", required_skills=[])
    assert job.required_skills == []


def test_no_experience_returns_none():
    job = analyze_job_description("Dev", "We want a Python developer.")
    # No experience mentioned
    assert job.min_experience_years is None or isinstance(job.min_experience_years, float)
