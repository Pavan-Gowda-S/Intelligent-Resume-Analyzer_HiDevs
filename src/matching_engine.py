"""
Explainable matching engine.

Produces a deterministic, fully documented score from 0–100 for each
candidate × job pair.  All scoring parameters are configurable through
src/config.py.

Score formula
-------------
  required_skills_component  = (matched_required / total_required) * WEIGHT_REQUIRED_SKILLS
  preferred_skills_component = (matched_preferred / total_preferred) * WEIGHT_PREFERRED_SKILLS
  experience_component       = experience_fraction * WEIGHT_EXPERIENCE
  keyword_component          = (matched_keywords / top_N_keywords) * WEIGHT_KEYWORDS
  total = sum of the four components   [0 – 100]

Edge cases
----------
- No required skills: the required-skills component awards full marks to all
  candidates and a warning is added.
- No preferred skills: the preferred component awards full marks.
- Unknown experience: UNKNOWN_EXPERIENCE_FRACTION of WEIGHT_EXPERIENCE is awarded
  and a warning is added.
- Score is clamped to [0, 100].
"""

from __future__ import annotations

import re

from src.config import (
    LABEL_LIMITED,
    LABEL_MODERATE,
    LABEL_STRONG,
    UNKNOWN_EXPERIENCE_FRACTION,
    WEIGHT_EXPERIENCE,
    WEIGHT_KEYWORDS,
    WEIGHT_PREFERRED_SKILLS,
    WEIGHT_REQUIRED_SKILLS,
)
from src.models import JobDescription, ParsedResume, ScoreBreakdown
from src.utils import clamp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_skill_set(skills: list[str]) -> set[str]:
    """Lowercase and strip skill names for comparison."""
    return {s.strip().lower() for s in skills if s.strip()}


_KEYWORD_STOPWORDS: frozenset[str] = frozenset({
    "and", "or", "the", "a", "an", "in", "of", "to", "with",
    "for", "on", "at", "is", "are", "we", "you", "our", "team",
    "as", "be", "by", "it", "its", "that", "this", "will", "have",
    "can", "may", "should", "must", "well", "strong", "ability",
    "experience", "work", "role", "position", "candidate",
    "using", "such", "including", "preferred", "required",
})


def _extract_resume_tokens(text: str) -> set[str]:
    """Return a set of meaningful lowercase tokens from resume text."""
    tokens = re.findall(r"\b[a-z][a-z0-9\-\.#\+]{2,}\b", text.lower())
    return {t for t in tokens if t not in _KEYWORD_STOPWORDS}


def _compute_keyword_score(
    job_keywords: list[str],
    resume_text: str,
    top_n: int = 20,
) -> tuple[float, list[str]]:
    """
    Match job keywords against resume text.

    Returns (raw_score_0_to_1, matched_keywords).
    """
    keywords = [k for k in job_keywords[:top_n] if k.lower() not in _KEYWORD_STOPWORDS]
    if not keywords:
        return 1.0, []

    resume_tokens = _extract_resume_tokens(resume_text)
    matched = [k for k in keywords if k.lower() in resume_tokens]
    score = len(matched) / len(keywords)
    return score, matched


def _experience_fraction(
    required_years: float | None,
    candidate_months: int | None,
) -> tuple[float, float | None, bool]:
    """
    Compute the experience component fraction (0–1), the candidate's estimated
    years, and whether experience was unknown.

    Returns (fraction, candidate_years_or_None, was_unknown).
    """
    if candidate_months is None:
        return UNKNOWN_EXPERIENCE_FRACTION, None, True

    candidate_years = candidate_months / 12.0

    if required_years is None or required_years <= 0:
        # No specific requirement: grant full marks if any experience found
        return 1.0, candidate_years, False

    # Fraction: meets or exceeds → 1.0; partial credit for partial experience
    fraction = min(1.0, candidate_years / required_years)
    return fraction, candidate_years, False


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_candidate(
    resume: ParsedResume,
    job: JobDescription,
) -> ScoreBreakdown:
    """
    Score a parsed resume against a structured job description.

    Returns a fully populated ScoreBreakdown.  No side effects.
    """
    breakdown = ScoreBreakdown()
    warnings: list[str] = list(resume.warnings)  # carry over parse warnings

    # ---- Required skills ------------------------------------------------
    req_set = _normalise_skill_set(job.required_skills)
    cand_set = _normalise_skill_set(resume.skills)

    if not req_set:
        req_fraction = 1.0
        warnings.append(
            "No required skills were specified for this job. "
            "The required-skills component awards full marks to all candidates."
        )
        matched_req: list[str] = []
        missing_req: list[str] = []
    else:
        matched_req_lower = req_set & cand_set
        missing_req_lower = req_set - cand_set
        # Restore original casing from job list
        req_lower_to_orig = {s.lower(): s for s in job.required_skills}
        matched_req = [req_lower_to_orig.get(s, s) for s in matched_req_lower]
        missing_req = [req_lower_to_orig.get(s, s) for s in missing_req_lower]
        req_fraction = len(matched_req) / len(req_set)

    breakdown.matched_required = sorted(matched_req)
    breakdown.missing_required = sorted(missing_req)
    breakdown.required_skills_score = round(req_fraction * WEIGHT_REQUIRED_SKILLS, 2)

    # ---- Preferred skills -----------------------------------------------
    pref_set = _normalise_skill_set(job.preferred_skills)

    if not pref_set:
        pref_fraction = 1.0
        matched_pref: list[str] = []
        missing_pref: list[str] = []
    else:
        matched_pref_lower = pref_set & cand_set
        missing_pref_lower = pref_set - cand_set
        pref_lower_to_orig = {s.lower(): s for s in job.preferred_skills}
        matched_pref = [pref_lower_to_orig.get(s, s) for s in matched_pref_lower]
        missing_pref = [pref_lower_to_orig.get(s, s) for s in missing_pref_lower]
        pref_fraction = len(matched_pref) / len(pref_set)

    breakdown.matched_preferred = sorted(matched_pref)
    breakdown.missing_preferred = sorted(missing_pref)
    breakdown.preferred_skills_score = round(pref_fraction * WEIGHT_PREFERRED_SKILLS, 2)

    # ---- Experience -----------------------------------------------------
    exp_fraction, cand_years, exp_unknown = _experience_fraction(
        job.min_experience_years, resume.total_experience_months
    )
    breakdown.experience_years_found = cand_years
    breakdown.experience_years_required = job.min_experience_years
    breakdown.experience_unknown = exp_unknown
    breakdown.experience_score = round(exp_fraction * WEIGHT_EXPERIENCE, 2)

    if exp_unknown:
        warnings.append(
            f"Candidate experience is unknown; awarded {UNKNOWN_EXPERIENCE_FRACTION * 100:.0f}% "
            f"of the experience component ({UNKNOWN_EXPERIENCE_FRACTION * WEIGHT_EXPERIENCE:.1f} / "
            f"{WEIGHT_EXPERIENCE} pts)."
        )

    # ---- Keywords -------------------------------------------------------
    kw_fraction, matched_kw = _compute_keyword_score(
        job.keywords, resume.raw_text
    )
    breakdown.matched_keywords = matched_kw
    breakdown.keyword_score = round(kw_fraction * WEIGHT_KEYWORDS, 2)

    # ---- Total ----------------------------------------------------------
    total = (
        breakdown.required_skills_score
        + breakdown.preferred_skills_score
        + breakdown.experience_score
        + breakdown.keyword_score
    )
    breakdown.total_score = round(clamp(total), 2)

    # ---- Label ----------------------------------------------------------
    breakdown.alignment_label = _label(breakdown.total_score)

    # ---- Explanation ---------------------------------------------------
    breakdown.explanation = _build_explanation(breakdown, job)
    breakdown.data_quality_warnings = warnings

    return breakdown


def _label(score: float) -> str:
    if score >= LABEL_STRONG:
        return "Strong Alignment"
    if score >= LABEL_MODERATE:
        return "Moderate Alignment"
    if score >= LABEL_LIMITED:
        return "Limited Alignment"
    return "Needs Manual Review"


def _build_explanation(bd: ScoreBreakdown, job: JobDescription) -> str:
    lines: list[str] = [
        f"Overall alignment score: {bd.total_score:.0f} / 100  [{bd.alignment_label}]",
        "",
        "Score components:",
        f"  • Required skills  : {bd.required_skills_score:.1f} / {WEIGHT_REQUIRED_SKILLS} pts",
        f"  • Preferred skills : {bd.preferred_skills_score:.1f} / {WEIGHT_PREFERRED_SKILLS} pts",
        f"  • Experience       : {bd.experience_score:.1f} / {WEIGHT_EXPERIENCE} pts",
        f"  • Keyword alignment: {bd.keyword_score:.1f} / {WEIGHT_KEYWORDS} pts",
        "",
    ]

    if bd.matched_required:
        lines.append(f"Required skills matched ({len(bd.matched_required)}): "
                     f"{', '.join(bd.matched_required)}")
    if bd.missing_required:
        lines.append(f"Required skills missing ({len(bd.missing_required)}): "
                     f"{', '.join(bd.missing_required)}")

    if bd.matched_preferred:
        lines.append(f"Preferred skills matched ({len(bd.matched_preferred)}): "
                     f"{', '.join(bd.matched_preferred)}")

    if bd.experience_unknown:
        lines.append("Experience: Could not be reliably determined from the resume.")
    elif bd.experience_years_found is not None:
        req_str = (
            f"{bd.experience_years_required:.1f} yrs required"
            if bd.experience_years_required
            else "no minimum specified"
        )
        lines.append(
            f"Experience: ~{bd.experience_years_found:.1f} years estimated "
            f"({req_str})."
        )

    if bd.matched_keywords:
        lines.append(f"Job keywords found in resume: {', '.join(bd.matched_keywords[:10])}")

    lines.extend([
        "",
        "Note: This score reflects alignment with the stated job requirements "
        "only. It is a screening aid and must not be used as the sole basis for "
        "hiring decisions. A recruiter must independently verify all information.",
    ])

    return "\n".join(lines)
