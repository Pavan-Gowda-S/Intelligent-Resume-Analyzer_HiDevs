"""
Dashboard page component.
"""

from __future__ import annotations

import streamlit as st

from components.styles import (
    alert_html,
    page_header,
    score_badge_html,
    score_bar_html,
)
from src.json_storage import get_dashboard_stats


def render_dashboard() -> None:
    page_header(
        "Recruiter Dashboard",
        "Overview of all analyses, jobs, and candidate scores.",
    )

    stats = get_dashboard_stats()

    # ── Top metrics ────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resumes Analyzed", stats["total_resumes"])
    c2.metric("Job Descriptions", stats["total_jobs"])
    c3.metric("Avg Match Score", f"{stats['avg_score']:.1f}" if stats["total_resumes"] else "—")
    c4.metric("Needs Manual Review", stats["needs_manual_review"])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Empty state ────────────────────────────────────────────────────
    if stats["total_resumes"] == 0:
        st.markdown(
            alert_html(
                "No analyses yet.  Go to <strong>Analyze Resumes</strong> to get started, "
                "or use <strong>Load Sample Data</strong> in the sidebar to try a demo.",
                "info",
            ),
            unsafe_allow_html=True,
        )
        return

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.subheader("Score Distribution")
        scores = stats["score_distribution"]
        if scores:
            import pandas as pd

            bins = [0, 25, 50, 75, 100]
            labels = ["0-25 (Review)", "25-50 (Limited)", "50-75 (Moderate)", "75-100 (Strong)"]
            counts = [0, 0, 0, 0]
            for s in scores:
                if s <= 25:
                    counts[0] += 1
                elif s <= 50:
                    counts[1] += 1
                elif s <= 75:
                    counts[2] += 1
                else:
                    counts[3] += 1
            df = pd.DataFrame({"Range": labels, "Candidates": counts})
            st.bar_chart(df.set_index("Range"))
        else:
            st.info("No score data available yet.")

    with col_right:
        st.subheader("Recent Sessions")
        recent = stats.get("recent_sessions", [])
        if recent:
            for s in recent:
                with st.container():
                    st.markdown(
                        f"<div style='background:#1e293b;border:1px solid #334155;"
                        f"border-radius:8px;padding:10px 14px;margin-bottom:8px'>"
                        f"<div style='font-weight:600;color:#f1f5f9;font-size:0.9rem'>"
                        f"{s.get('job_title','(no title)')}</div>"
                        f"<div style='color:#64748b;font-size:0.78rem'>"
                        f"{s.get('total_candidates',0)} candidates • "
                        f"Avg {s.get('avg_score',0):.0f} pts • "
                        f"{s.get('created_at','')[:10]}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No recent sessions.")
