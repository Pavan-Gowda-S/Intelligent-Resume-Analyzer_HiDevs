"""Tests for report_generator.py"""

from __future__ import annotations

import pytest
from src.models import CandidateAnalysis, JobDescription, ScoreBreakdown
from src.report_generator import generate_html_report, generate_csv_export


def _make_analysis_with_score(score: float = 75.0) -> CandidateAnalysis:
    bd = ScoreBreakdown(
        total_score=score,
        required_skills_score=37.5,
        preferred_skills_score=15.0,
        experience_score=15.0,
        keyword_score=7.5,
        matched_required=["Python", "FastAPI"],
        missing_required=["Docker"],
        matched_preferred=["AWS"],
        experience_years_found=4.0,
        experience_years_required=3.0,
        alignment_label="Strong Alignment",
        explanation="Test explanation text.",
    )
    a = CandidateAnalysis(
        job_id="j1",
        session_id="s1",
        job_title="Senior Python Developer",
        resume_id="r1",
        filename="resume.txt",
        candidate_name="Jordan Test",
        score_breakdown=bd,
        email="jordan@example.com",
        phone="+1 555-0100",
        skills=["Python", "FastAPI"],
        education_summary="BSc Computer Science",
        certifications=["AWS Certified Developer"],
    )
    return a


def test_html_report_returns_string():
    a = _make_analysis_with_score()
    html = generate_html_report(a, save_to_disk=False)
    assert isinstance(html, str)
    assert len(html) > 200


def test_html_report_contains_score():
    a = _make_analysis_with_score(score=82.0)
    html = generate_html_report(a, save_to_disk=False)
    assert "82" in html


def test_html_report_contains_candidate_name():
    a = _make_analysis_with_score()
    html = generate_html_report(a, save_to_disk=False)
    assert "Jordan Test" in html


def test_html_report_escapes_xss():
    """Malicious content in candidate name must be HTML-escaped."""
    a = _make_analysis_with_score()
    a.candidate_name = "<script>alert('xss')</script>"
    html = generate_html_report(a, save_to_disk=False)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_html_contains_disclaimer():
    a = _make_analysis_with_score()
    html = generate_html_report(a, save_to_disk=False)
    assert "Disclaimer" in html


def test_csv_export_returns_string():
    analyses = [_make_analysis_with_score(70.0), _make_analysis_with_score(50.0)]
    csv_str = generate_csv_export(analyses)
    assert isinstance(csv_str, str)


def test_csv_has_header_row():
    analyses = [_make_analysis_with_score()]
    csv_str = generate_csv_export(analyses)
    assert "Candidate Name" in csv_str
    assert "Total Score" in csv_str


def test_csv_has_candidate_rows():
    analyses = [_make_analysis_with_score(score=75.0)]
    csv_str = generate_csv_export(analyses)
    assert "Jordan Test" in csv_str
    assert "75" in csv_str


def test_csv_export_empty():
    csv_str = generate_csv_export([])
    # Should at least have the header
    assert "Candidate Name" in csv_str


def test_pdf_report_returns_bytes():
    """PDF generation requires ReportLab; skip if unavailable."""
    pytest.importorskip("reportlab")
    from src.report_generator import generate_pdf_report
    a = _make_analysis_with_score()
    pdf = generate_pdf_report(a, save_to_disk=False)
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_html_report_unknown_experience():
    a = _make_analysis_with_score()
    a.score_breakdown.experience_unknown = True
    a.score_breakdown.experience_years_found = None
    html = generate_html_report(a, save_to_disk=False)
    assert "Unknown" in html or "could not" in html.lower()
