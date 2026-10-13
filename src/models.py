"""
Pydantic-style dataclasses (stdlib) used throughout the application.

Using Python dataclasses + validation helpers keeps the project dependency-
light while giving us structured, type-checked data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Skill taxonomy entry
# ---------------------------------------------------------------------------

@dataclass
class SkillEntry:
    """A normalised skill with its category and optional aliases."""
    name: str
    category: str
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "category": self.category, "aliases": self.aliases}


# ---------------------------------------------------------------------------
# Parsed education record
# ---------------------------------------------------------------------------

@dataclass
class Education:
    degree: str = ""
    institution: str = ""
    year: str = ""
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "degree": self.degree,
            "institution": self.institution,
            "year": self.year,
            "raw_text": self.raw_text,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Education":
        return cls(
            degree=d.get("degree", ""),
            institution=d.get("institution", ""),
            year=d.get("year", ""),
            raw_text=d.get("raw_text", ""),
        )


# ---------------------------------------------------------------------------
# Parsed work-experience record
# ---------------------------------------------------------------------------

@dataclass
class WorkExperience:
    title: str = ""
    employer: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_months: int | None = None
    responsibilities: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "employer": self.employer,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration_months": self.duration_months,
            "responsibilities": self.responsibilities,
            "raw_text": self.raw_text,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkExperience":
        return cls(
            title=d.get("title", ""),
            employer=d.get("employer", ""),
            start_date=d.get("start_date", ""),
            end_date=d.get("end_date", ""),
            duration_months=d.get("duration_months"),
            responsibilities=d.get("responsibilities", []),
            raw_text=d.get("raw_text", ""),
        )


# ---------------------------------------------------------------------------
# Parsed resume (candidate)
# ---------------------------------------------------------------------------

@dataclass
class ParsedResume:
    """All information extracted from a single resume file."""

    id: str = field(default_factory=_new_id)
    filename: str = ""
    file_format: str = ""

    # Contact
    candidate_name: str = ""
    name_confidence: str = "unknown"   # "high" | "medium" | "low" | "unknown"
    email: str = ""
    phone: str = ""

    # Content
    skills: list[str] = field(default_factory=list)
    skills_by_category: dict[str, list[str]] = field(default_factory=dict)
    education: list[Education] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    work_experience: list[WorkExperience] = field(default_factory=list)
    total_experience_months: int | None = None   # None = unknown

    # Raw text
    raw_text: str = ""
    text_extraction_method: str = ""

    # Quality signals
    warnings: list[str] = field(default_factory=list)
    parse_success: bool = True
    is_scanned_pdf: bool = False

    parsed_at: str = field(default_factory=_now_iso)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_format": self.file_format,
            "candidate_name": self.candidate_name,
            "name_confidence": self.name_confidence,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "skills_by_category": self.skills_by_category,
            "education": [e.to_dict() for e in self.education],
            "certifications": self.certifications,
            "work_experience": [w.to_dict() for w in self.work_experience],
            "total_experience_months": self.total_experience_months,
            "raw_text": self.raw_text,
            "text_extraction_method": self.text_extraction_method,
            "warnings": self.warnings,
            "parse_success": self.parse_success,
            "is_scanned_pdf": self.is_scanned_pdf,
            "parsed_at": self.parsed_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ParsedResume":
        r = cls(
            id=d.get("id", _new_id()),
            filename=d.get("filename", ""),
            file_format=d.get("file_format", ""),
            candidate_name=d.get("candidate_name", ""),
            name_confidence=d.get("name_confidence", "unknown"),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            skills=d.get("skills", []),
            skills_by_category=d.get("skills_by_category", {}),
            certifications=d.get("certifications", []),
            total_experience_months=d.get("total_experience_months"),
            raw_text=d.get("raw_text", ""),
            text_extraction_method=d.get("text_extraction_method", ""),
            warnings=d.get("warnings", []),
            parse_success=d.get("parse_success", True),
            is_scanned_pdf=d.get("is_scanned_pdf", False),
            parsed_at=d.get("parsed_at", _now_iso()),
        )
        r.education = [Education.from_dict(e) for e in d.get("education", [])]
        r.work_experience = [WorkExperience.from_dict(w) for w in d.get("work_experience", [])]
        return r


# ---------------------------------------------------------------------------
# Job description
# ---------------------------------------------------------------------------

@dataclass
class JobDescription:
    id: str = field(default_factory=_new_id)
    title: str = ""
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_experience_years: float | None = None
    responsibilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "min_experience_years": self.min_experience_years,
            "responsibilities": self.responsibilities,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "JobDescription":
        return cls(
            id=d.get("id", _new_id()),
            title=d.get("title", ""),
            description=d.get("description", ""),
            required_skills=d.get("required_skills", []),
            preferred_skills=d.get("preferred_skills", []),
            min_experience_years=d.get("min_experience_years"),
            responsibilities=d.get("responsibilities", []),
            keywords=d.get("keywords", []),
            created_at=d.get("created_at", _now_iso()),
            updated_at=d.get("updated_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Score breakdown
# ---------------------------------------------------------------------------

@dataclass
class ScoreBreakdown:
    required_skills_score: float = 0.0
    preferred_skills_score: float = 0.0
    experience_score: float = 0.0
    keyword_score: float = 0.0
    total_score: float = 0.0

    matched_required: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)

    experience_years_found: float | None = None
    experience_years_required: float | None = None
    experience_unknown: bool = False

    matched_keywords: list[str] = field(default_factory=list)

    explanation: str = ""
    alignment_label: str = ""
    data_quality_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_skills_score": self.required_skills_score,
            "preferred_skills_score": self.preferred_skills_score,
            "experience_score": self.experience_score,
            "keyword_score": self.keyword_score,
            "total_score": self.total_score,
            "matched_required": self.matched_required,
            "missing_required": self.missing_required,
            "matched_preferred": self.matched_preferred,
            "missing_preferred": self.missing_preferred,
            "experience_years_found": self.experience_years_found,
            "experience_years_required": self.experience_years_required,
            "experience_unknown": self.experience_unknown,
            "matched_keywords": self.matched_keywords,
            "explanation": self.explanation,
            "alignment_label": self.alignment_label,
            "data_quality_warnings": self.data_quality_warnings,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ScoreBreakdown":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Full analysis result for one candidate × one job
# ---------------------------------------------------------------------------

@dataclass
class CandidateAnalysis:
    id: str = field(default_factory=_new_id)
    session_id: str = ""
    job_id: str = ""
    job_title: str = ""
    resume_id: str = ""
    filename: str = ""
    candidate_name: str = ""

    score_breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    # Cached resume fields for quick display
    email: str = ""
    phone: str = ""
    skills: list[str] = field(default_factory=list)
    education_summary: str = ""
    certifications: list[str] = field(default_factory=list)
    experience_summary: str = ""
    warnings: list[str] = field(default_factory=list)

    analyzed_at: str = field(default_factory=_now_iso)
    report_html_path: str = ""
    report_pdf_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "resume_id": self.resume_id,
            "filename": self.filename,
            "candidate_name": self.candidate_name,
            "score_breakdown": self.score_breakdown.to_dict(),
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "education_summary": self.education_summary,
            "certifications": self.certifications,
            "experience_summary": self.experience_summary,
            "warnings": self.warnings,
            "analyzed_at": self.analyzed_at,
            "report_html_path": self.report_html_path,
            "report_pdf_path": self.report_pdf_path,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CandidateAnalysis":
        ca = cls(
            id=d.get("id", _new_id()),
            session_id=d.get("session_id", ""),
            job_id=d.get("job_id", ""),
            job_title=d.get("job_title", ""),
            resume_id=d.get("resume_id", ""),
            filename=d.get("filename", ""),
            candidate_name=d.get("candidate_name", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            skills=d.get("skills", []),
            education_summary=d.get("education_summary", ""),
            certifications=d.get("certifications", []),
            experience_summary=d.get("experience_summary", ""),
            warnings=d.get("warnings", []),
            analyzed_at=d.get("analyzed_at", _now_iso()),
            report_html_path=d.get("report_html_path", ""),
            report_pdf_path=d.get("report_pdf_path", ""),
        )
        if "score_breakdown" in d and isinstance(d["score_breakdown"], dict):
            ca.score_breakdown = ScoreBreakdown.from_dict(d["score_breakdown"])
        return ca


# ---------------------------------------------------------------------------
# Analysis session
# ---------------------------------------------------------------------------

@dataclass
class AnalysisSession:
    id: str = field(default_factory=_new_id)
    job_id: str = ""
    job_title: str = ""
    candidate_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    avg_score: float = 0.0
    total_candidates: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "candidate_ids": self.candidate_ids,
            "created_at": self.created_at,
            "avg_score": self.avg_score,
            "total_candidates": self.total_candidates,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AnalysisSession":
        return cls(
            id=d.get("id", _new_id()),
            job_id=d.get("job_id", ""),
            job_title=d.get("job_title", ""),
            candidate_ids=d.get("candidate_ids", []),
            created_at=d.get("created_at", _now_iso()),
            avg_score=d.get("avg_score", 0.0),
            total_candidates=d.get("total_candidates", 0),
        )
