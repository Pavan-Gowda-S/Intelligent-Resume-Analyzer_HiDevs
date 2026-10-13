"""Tests for validators.py"""

from __future__ import annotations

import pytest
from src.validators import (
    validate_file_extension,
    validate_file_size,
    validate_job_title,
    validate_job_description,
    validate_experience_years,
    sanitize_filename,
)


def test_valid_pdf_extension():
    ok, msg = validate_file_extension("resume.pdf")
    assert ok is True


def test_valid_docx_extension():
    ok, msg = validate_file_extension("cv.docx")
    assert ok is True


def test_valid_txt_extension():
    ok, msg = validate_file_extension("resume.txt")
    assert ok is True


def test_invalid_extension():
    ok, msg = validate_file_extension("photo.jpg")
    assert ok is False
    assert "unsupported" in msg.lower()


def test_file_size_empty():
    ok, msg = validate_file_size(b"", "empty.txt")
    assert ok is False


def test_file_size_ok():
    ok, msg = validate_file_size(b"content", "file.txt")
    assert ok is True


def test_file_size_too_large():
    big = b"X" * (11 * 1024 * 1024)
    ok, msg = validate_file_size(big, "big.txt")
    assert ok is False
    assert "exceed" in msg.lower() or "limit" in msg.lower()


def test_job_title_valid():
    ok, msg = validate_job_title("Software Engineer")
    assert ok is True


def test_job_title_empty():
    ok, msg = validate_job_title("")
    assert ok is False


def test_job_title_too_long():
    ok, msg = validate_job_title("A" * 201)
    assert ok is False


def test_job_description_valid():
    ok, msg = validate_job_description("We need a skilled developer with Python experience.")
    assert ok is True


def test_job_description_empty():
    ok, msg = validate_job_description("")
    assert ok is False


def test_job_description_too_short():
    ok, msg = validate_job_description("Dev job")
    assert ok is False


def test_experience_years_none():
    ok, msg = validate_experience_years(None)
    assert ok is True


def test_experience_years_valid():
    ok, msg = validate_experience_years(5.0)
    assert ok is True


def test_experience_years_negative():
    ok, msg = validate_experience_years(-1.0)
    assert ok is False


def test_experience_years_too_high():
    ok, msg = validate_experience_years(65.0)
    assert ok is False


def test_sanitize_filename_normal():
    result = sanitize_filename("Jordan Mitchell")
    assert "/" not in result
    assert "\\" not in result


def test_sanitize_filename_special_chars():
    result = sanitize_filename("../../etc/passwd")
    assert "/" not in result
    assert result  # not empty


def test_sanitize_filename_empty():
    result = sanitize_filename("")
    assert result == "file"
