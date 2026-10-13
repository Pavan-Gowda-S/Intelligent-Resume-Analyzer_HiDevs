"""Tests for skill_extractor.py"""

from __future__ import annotations

import pytest
from src.skill_extractor import (
    extract_skills,
    group_skills_by_category,
    normalize_skill,
    get_all_skill_names,
    get_categories,
)


def test_extract_known_skill():
    assert "Python" in extract_skills("I have experience with Python.")


def test_extract_javascript_not_java():
    """'JavaScript' must not be confused with 'Java'."""
    skills = extract_skills("Proficient in JavaScript development.")
    skill_names = [s.lower() for s in skills]
    assert "javascript" in skill_names
    assert "java" not in skill_names


def test_extract_java_not_javascript():
    skills = extract_skills("We use Java for backend services.")
    skill_names = [s.lower() for s in skills]
    assert "java" in skill_names


def test_no_false_positive_c_in_word():
    """Letter 'C' should not match inside words like 'access' or 'each'."""
    skills = extract_skills("Each access control decision is verified.")
    skill_names = [s.lower() for s in skills]
    assert "c" not in skill_names


def test_c_language_standalone():
    """Standalone 'C' as a language should be detectable."""
    skills = extract_skills("Experience programming in C and assembly.")
    # 'C' should match as a standalone word
    skill_names = [s.lower() for s in skills]
    assert "c" in skill_names


def test_alias_matching():
    """'js' alias should map to 'JavaScript'."""
    skills = extract_skills("Strong js skills required.")
    assert "JavaScript" in skills


def test_case_insensitive():
    skills = extract_skills("Experienced with PYTHON and Postgresql.")
    skill_lower = [s.lower() for s in skills]
    assert "python" in skill_lower
    assert "postgresql" in skill_lower


def test_deduplication():
    skills = extract_skills("Python Python Python Python")
    assert skills.count("Python") == 1


def test_group_by_category():
    skills = ["Python", "React", "PostgreSQL"]
    grouped = group_skills_by_category(skills)
    assert "Programming Languages" in grouped
    assert "Python" in grouped["Programming Languages"]


def test_normalize_skill_known():
    assert normalize_skill("python") == "Python"


def test_normalize_skill_alias():
    result = normalize_skill("js")
    assert result == "JavaScript"


def test_normalize_skill_unknown_returns_input():
    result = normalize_skill("QuantumFluxLib")
    assert result == "QuantumFluxLib"


def test_extract_multiple_skills():
    text = "Required: Python, FastAPI, Docker, PostgreSQL, AWS, pytest."
    skills = extract_skills(text)
    assert len(skills) >= 4


def test_empty_text():
    assert extract_skills("") == []


def test_get_all_skill_names_not_empty():
    names = get_all_skill_names()
    assert len(names) > 20


def test_get_categories_not_empty():
    cats = get_categories()
    assert len(cats) > 0


def test_go_not_false_positive():
    """'go' should not match in 'going' or 'forgot'."""
    skills = extract_skills("He is going to the store and forgot the keys.")
    skill_names = [s.lower() for s in skills]
    assert "go" not in skill_names
