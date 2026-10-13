"""
Candidate card components for the analysis results page.
"""

from __future__ import annotations

import streamlit as st

from components.styles import score_badge_html, score_bar_html, skill_chips_html
from src.models import CandidateAnalysis


def render_candidate_table(
    analyses: list[CandidateAnalysis],
    on_select: "callable | None" = None,
) -> str | None:
    """
    Render a sortable table of candidate analyses.

    Returns the id of the selected candidate if the user clicks 'View', else None.
    """
    if not analyses:
        st.info("No candidates to display.")
        return None

    sort_by = st.selectbox(
        "Sort by",
        ["Match Score (High→Low)", "Match Score (Low→High)", "Candidate Name", "Status"],
        key="cand_sort",
    )

    sorted_analyses = list(analyses)
    if sort_by == "Match Score (High→Low)":
        sorted_analyses.sort(key=lambda a: a.score_breakdown.total_score, reverse=True)
    elif sort_by == "Match Score (Low→High)":
        sorted_analyses.sort(key=lambda a: a.score_breakdown.total_score)
    elif sort_by == "Candidate Name":
        sorted_analyses.sort(key=lambda a: (a.candidate_name or "zzz").lower())
    elif sort_by == "Status":
        sorted_analyses.sort(key=lambda a: a.score_breakdown.alignment_label)

    selected_id: str | None = None

    # Header
    cols = st.columns([2, 1.2, 1.5, 1.5, 1.5, 1])
    for col, label in zip(
        cols,
        ["Candidate", "Score", "Req. Skills", "Exp.", "Status", "Action"],
    ):
        col.markdown(f"<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;text-transform:uppercase'>{label}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e3a5f;margin:4px 0 8px 0'>", unsafe_allow_html=True)

    for a in sorted_analyses:
        bd = a.score_breakdown
        req_total = len(bd.matched_required) + len(bd.missing_required)
        req_text = f"{len(bd.matched_required)}/{req_total}" if req_total > 0 else "N/A"

        if bd.experience_unknown:
            exp_text = "Unknown"
        elif bd.experience_years_found is not None:
            exp_text = f"~{bd.experience_years_found:.1f} yrs"
        else:
            exp_text = "—"

        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.2, 1.5, 1.5, 1.5, 1])

        with c1:
            name = a.candidate_name or "Name not detected"
            st.markdown(
                f"<div style='color:#f1f5f9;font-weight:600'>{name}</div>"
                f"<div style='color:#64748b;font-size:0.78rem'>{a.filename}</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div style='font-size:1.2rem;font-weight:700;color:#f1f5f9'>{bd.total_score:.0f}</div>"
                + score_bar_html(bd.total_score),
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div style='color:#cbd5e1'>{req_text}</div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"<div style='color:#cbd5e1'>{exp_text}</div>",
                unsafe_allow_html=True,
            )
        with c5:
            st.markdown(
                score_badge_html(bd.total_score, bd.alignment_label),
                unsafe_allow_html=True,
            )
        with c6:
            if st.button("View", key=f"view_{a.id}"):
                selected_id = a.id

        st.markdown("<hr style='border-color:#0f172a;margin:4px 0'>", unsafe_allow_html=True)

    return selected_id


def render_candidate_detail(analysis: CandidateAnalysis) -> None:
    """Render a full candidate detail view."""
    bd = analysis.score_breakdown

    name = analysis.candidate_name or "Name not detected"
    st.markdown(
        f"<h2 style='color:#f1f5f9;margin-bottom:4px'>{name}</h2>"
        f"<div style='color:#64748b;font-size:0.9rem'>File: {analysis.filename} &nbsp;|&nbsp; "
        f"Analyzed: {analysis.analyzed_at[:19]}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#1e3a5f;margin:12px 0'>", unsafe_allow_html=True)

    # Score headline
    col_score, col_label = st.columns([1, 2])
    with col_score:
        st.markdown(
            f"<div style='font-size:3rem;font-weight:800;color:#f1f5f9;line-height:1'>"
            f"{bd.total_score:.0f}<span style='font-size:1.2rem;color:#64748b'>/100</span></div>"
            + score_bar_html(bd.total_score),
            unsafe_allow_html=True,
        )
    with col_label:
        st.markdown(
            score_badge_html(bd.total_score, bd.alignment_label),
            unsafe_allow_html=True,
        )
        st.caption("Alignment with job requirements — not a hiring decision")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Score breakdown
    with st.expander("📊 Score Breakdown", expanded=True):
        cols = st.columns(4)
        breakdown_items = [
            ("Required Skills", bd.required_skills_score, 50),
            ("Preferred Skills", bd.preferred_skills_score, 20),
            ("Experience", bd.experience_score, 20),
            ("Keywords", bd.keyword_score, 10),
        ]
        for col, (label, score, max_score) in zip(cols, breakdown_items):
            col.metric(label, f"{score:.1f} / {max_score}")

    # Contact information
    with st.expander("📇 Contact Information"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Email:** {analysis.email or '—'}")
        c2.markdown(f"**Phone:** {analysis.phone or '—'}")

    # Skills
    with st.expander("🛠️ Skills", expanded=True):
        if bd.matched_required:
            st.markdown("**✅ Required skills matched:**")
            st.markdown(skill_chips_html(bd.matched_required, "ok"), unsafe_allow_html=True)
        if bd.missing_required:
            st.markdown("**❌ Required skills missing:**")
            st.markdown(skill_chips_html(bd.missing_required, "missing"), unsafe_allow_html=True)
        if bd.matched_preferred:
            st.markdown("**✅ Preferred skills matched:**")
            st.markdown(skill_chips_html(bd.matched_preferred, "ok"), unsafe_allow_html=True)
        if bd.missing_preferred:
            st.markdown("**◌ Preferred skills not found:**")
            st.markdown(skill_chips_html(bd.missing_preferred, ""), unsafe_allow_html=True)

        all_skills = analysis.skills
        if all_skills:
            st.markdown("**All detected skills:**")
            st.markdown(skill_chips_html(all_skills), unsafe_allow_html=True)

    # Experience
    with st.expander("💼 Experience"):
        if bd.experience_unknown:
            st.warning("Experience could not be reliably determined from this resume.")
        elif bd.experience_years_found is not None:
            req_str = (
                f"Job requires: {bd.experience_years_required:.1f} yrs"
                if bd.experience_years_required
                else "No minimum specified"
            )
            st.markdown(f"**Estimated:** ~{bd.experience_years_found:.1f} years")
            st.markdown(f"**{req_str}**")
        else:
            st.info("No experience information found.")
        if analysis.experience_summary:
            st.markdown(f"*{analysis.experience_summary}*")

    # Education
    with st.expander("🎓 Education & Certifications"):
        if analysis.education_summary:
            st.markdown(analysis.education_summary)
        else:
            st.info("No education information detected.")
        if analysis.certifications:
            st.markdown("**Certifications:**")
            for cert in analysis.certifications:
                st.markdown(f"- {cert}")

    # Explanation
    with st.expander("📝 Full Explanation"):
        st.code(bd.explanation, language=None)

    # Warnings
    if bd.data_quality_warnings:
        with st.expander("⚠️ Data Quality Warnings"):
            for w in bd.data_quality_warnings:
                st.warning(w)

    # Matched keywords
    if bd.matched_keywords:
        with st.expander("🔍 Matched Job Keywords"):
            st.markdown(skill_chips_html(bd.matched_keywords), unsafe_allow_html=True)

    st.markdown(
        "<div style='margin-top:16px;padding:10px;background:#0c1d36;"
        "border-radius:8px;color:#64748b;font-size:0.8rem'>"
        "⚠️ This score reflects text-based alignment with stated job requirements. "
        "It is a screening aid only.  All information must be independently verified. "
        "This report must not be used as the sole basis for any hiring decision."
        "</div>",
        unsafe_allow_html=True,
    )
