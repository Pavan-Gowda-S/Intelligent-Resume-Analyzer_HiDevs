"""Tests for resume_parser.py"""

from __future__ import annotations

import pytest
from src.resume_parser import parse_resume
from src.models import ParsedResume


SAMPLE_TXT = b"""Jordan Mitchell
jordan.mitchell@example.com
+1 415-555-0192

Skills
Python, FastAPI, Flask, REST APIs, PostgreSQL, Docker, pytest, Git, AWS

Work Experience

Senior Software Engineer
TechCorp Solutions
Jan 2021 - Present
- Built REST APIs in Python using FastAPI.

Education
Bachelor of Science in Computer Science
University of California - 2018
"""


def test_parse_txt_returns_parsed_resume():
    result = parse_resume(SAMPLE_TXT, "test_resume.txt")
    assert isinstance(result, ParsedResume)


def test_parse_txt_success_flag():
    result = parse_resume(SAMPLE_TXT, "test_resume.txt")
    assert result.parse_success is True


def test_parse_txt_extracts_email():
    result = parse_resume(SAMPLE_TXT, "test_resume.txt")
    assert result.email == "jordan.mitchell@example.com"


def test_parse_txt_extracts_phone():
    result = parse_resume(SAMPLE_TXT, "test_resume.txt")
    assert "415" in result.phone or result.phone != ""


def test_parse_txt_extracts_skills():
    result = parse_resume(SAMPLE_TXT, "test_resume.txt")
    assert len(result.skills) > 0
    skill_lower = [s.lower() for s in result.skills]
    assert any("python" in s for s in skill_lower)


def test_parse_empty_file():
    result = parse_resume(b"", "empty.txt")
    assert result.parse_success is False
    assert len(result.warnings) > 0


def test_parse_unsupported_extension():
    result = parse_resume(b"some content", "file.xls")
    assert result.parse_success is False
    assert any("unsupported" in w.lower() for w in result.warnings)


def test_parse_oversized_file():
    big = b"A" * (11 * 1024 * 1024)  # 11 MB > 10 MB limit
    result = parse_resume(big, "big.txt")
    assert result.parse_success is False
    assert any("exceed" in w.lower() or "limit" in w.lower() for w in result.warnings)


def test_parse_stores_filename():
    result = parse_resume(SAMPLE_TXT, "my_resume.txt")
    assert result.filename == "my_resume.txt"


def test_parse_raw_text_not_empty():
    result = parse_resume(SAMPLE_TXT, "resume.txt")
    assert result.raw_text.strip() != ""


def test_parse_candidate_name():
    result = parse_resume(SAMPLE_TXT, "test.txt")
    # Name detection is heuristic; just check it's not an email
    assert "@" not in result.candidate_name


def test_parse_docx_bytes_invalid():
    """Passing garbage bytes as a DOCX should produce a failed parse, not crash."""
    result = parse_resume(b"not a real docx file", "bad.docx")
    assert result.parse_success is False


def test_parse_result_has_unique_id():
    r1 = parse_resume(SAMPLE_TXT, "a.txt")
    r2 = parse_resume(SAMPLE_TXT, "b.txt")
    assert r1.id != r2.id


def test_parse_txt_no_skills():
    """Resume with no known skills should succeed but return empty skills list."""
    no_skills = b"Jane Doe\njane@example.com\nI write documents.\n"
    result = parse_resume(no_skills, "plain.txt")
    assert result.parse_success is True
    assert isinstance(result.skills, list)


def test_parse_valid_pdf():
    """Verify parsing a valid in-memory PDF using PyMuPDF."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        fitz.Point(50, 72),
        "Alex Morgan\nalex.morgan@example.com\n+1 415-555-0199\n\nSkills:\nPython, Docker, SQL\n\nExperience:\nSoftware Engineer\nJan 2021 - Present\nBuilt backend services in Python."
    )
    pdf_bytes = doc.write()
    doc.close()

    result = parse_resume(pdf_bytes, "alex_resume.pdf")
    assert result.parse_success is True
    assert result.file_format == "pdf"
    assert "alex.morgan@example.com" in result.email
    assert "Python" in result.skills


def test_parse_scanned_or_empty_pdf():
    """Verify detection of PDF with no extractable text."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    doc.new_page()  # Page with no text (simulates scanned/image-only PDF)
    empty_pdf_bytes = doc.write()
    doc.close()

    result = parse_resume(empty_pdf_bytes, "scanned_doc.pdf")
    assert result.parse_success is False
    assert result.is_scanned_pdf is True
    assert any("scanned" in w.lower() or "no extractable text" in w.lower() for w in result.warnings)


def test_parse_valid_docx():
    """Verify parsing a valid in-memory DOCX using python-docx."""
    docx_module = pytest.importorskip("docx")
    import io
    doc = docx_module.Document()
    doc.add_paragraph("Taylor Swift")
    doc.add_paragraph("taylor.swift@example.com")
    doc.add_paragraph("+1 212-555-0144")
    doc.add_paragraph("Skills: Python, Django, REST APIs, PostgreSQL")
    doc.add_paragraph("Experience: Python Developer from Jan 2020 - Present")

    # Also test table reading
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Education"
    table.cell(0, 1).text = "B.S. Computer Science, Stanford University, 2020"
    table.cell(1, 0).text = "Certifications"
    table.cell(1, 1).text = "AWS Certified Solutions Architect"

    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()

    result = parse_resume(docx_bytes, "taylor_resume.docx")
    assert result.parse_success is True
    assert result.file_format == "docx"
    assert "taylor.swift@example.com" in result.email
    assert "Python" in result.skills
    assert "Django" in result.skills

