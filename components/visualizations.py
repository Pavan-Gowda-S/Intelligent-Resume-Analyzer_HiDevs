"""
Visualisation helpers for the dashboard and analysis pages.
"""

from __future__ import annotations

import streamlit as st


def render_score_gauge(score: float, label: str = "") -> None:
    """Render a simple horizontal score bar using Streamlit progress."""
    color = (
        "green" if score >= 75
        else "orange" if score >= 50
        else "red"
    )
    st.markdown(
        f"<div style='font-size:0.85rem;color:#94a3b8;margin-bottom:2px'>{label}</div>",
        unsafe_allow_html=True,
    )
    st.progress(int(score))


def render_skills_gap_chart(
    required: list[str],
    matched: list[str],
) -> None:
    """Show a simple matched vs missing breakdown."""
    if not required:
        st.info("No required skills specified.")
        return

    matched_count = len(matched)
    total = len(required)
    missing_count = total - matched_count

    import pandas as pd

    df = pd.DataFrame({
        "Category": ["Matched", "Missing"],
        "Count": [matched_count, missing_count],
    })
    st.bar_chart(df.set_index("Category"))


def render_score_distribution(scores: list[float]) -> None:
    """Render a simple bar chart of score ranges."""
    if not scores:
        st.info("No score data yet.")
        return
    import pandas as pd

    counts = {"0–25": 0, "26–50": 0, "51–75": 0, "76–100": 0}
    for s in scores:
        if s <= 25:
            counts["0–25"] += 1
        elif s <= 50:
            counts["26–50"] += 1
        elif s <= 75:
            counts["51–75"] += 1
        else:
            counts["76–100"] += 1

    df = pd.DataFrame({"Range": list(counts.keys()), "Candidates": list(counts.values())})
    st.bar_chart(df.set_index("Range"))
