"""
Shared CSS and styling utilities for the Streamlit UI.
"""

from __future__ import annotations


MAIN_CSS = """
<style>
/* ── Root & global ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

/* ── Sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1b2d 0%, #162236 100%);
    border-right: 1px solid #1e3a5f;
}
[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(59,130,246,0.15);
    color: #93c5fd !important;
}

/* ── Main area ──────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #0f172a;
}
[data-testid="stMain"] {
    background: #0f172a;
}

/* ── Cards ──────────────────────────────────────────── */
.ira-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.ira-card-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.ira-card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1.1;
}
.ira-card-sub {
    font-size: 0.82rem;
    color: #64748b;
    margin-top: 4px;
}

/* ── Score badge ─────────────────────────────────────── */
.score-badge-strong  { background: #166534; color: #bbf7d0; }
.score-badge-moderate { background: #78350f; color: #fde68a; }
.score-badge-limited  { background: #7c2d12; color: #fed7aa; }
.score-badge-review   { background: #3b0764; color: #e9d5ff; }
.score-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
}

/* ── Skill chips ─────────────────────────────────────── */
.skill-chip {
    display: inline-block;
    background: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    padding: 3px 10px;
    border-radius: 14px;
    font-size: 0.78rem;
    margin: 2px;
}
.skill-chip.missing {
    background: #3b0f0f;
    color: #fca5a5;
    border-color: #dc2626;
}
.skill-chip.ok {
    background: #052e16;
    color: #86efac;
    border-color: #16a34a;
}

/* ── Page header ─────────────────────────────────────── */
.page-header {
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 16px;
    margin-bottom: 24px;
}
.page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0;
}
.page-subtitle {
    font-size: 0.9rem;
    color: #64748b;
    margin: 4px 0 0 0;
}

/* ── Alert boxes ─────────────────────────────────────── */
.ira-alert {
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.88rem;
    margin: 8px 0;
}
.ira-alert-warning {
    background: #1c1700;
    border-left: 4px solid #ca8a04;
    color: #fde68a;
}
.ira-alert-error {
    background: #200;
    border-left: 4px solid #dc2626;
    color: #fca5a5;
}
.ira-alert-info {
    background: #0c1d36;
    border-left: 4px solid #3b82f6;
    color: #93c5fd;
}
.ira-alert-success {
    background: #0a1f0e;
    border-left: 4px solid #16a34a;
    color: #86efac;
}

/* ── Tables ──────────────────────────────────────────── */
.ira-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}
.ira-table th {
    background: #1e293b;
    color: #94a3b8;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid #334155;
}
.ira-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #1e293b;
    color: #cbd5e1;
    vertical-align: middle;
}
.ira-table tr:hover td {
    background: #1e293b;
}

/* ── Streamlit overrides ─────────────────────────────── */
div[data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
}
div[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.8rem !important;
}

/* ── Buttons ─────────────────────────────────────────── */
.stButton > button {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
    transition: background 0.15s;
}
.stButton > button:hover {
    background: #1d4ed8;
}

/* ── Inputs ──────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border-color: #334155 !important;
    border-radius: 8px !important;
}

/* ── Progress bar ────────────────────────────────────── */
.score-bar-container {
    background: #1e293b;
    border-radius: 999px;
    height: 10px;
    margin: 6px 0;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.4s ease;
}

/* ── Divider ─────────────────────────────────────────── */
.ira-divider {
    border: none;
    border-top: 1px solid #1e3a5f;
    margin: 20px 0;
}
</style>
"""


def inject_css() -> None:
    """Inject the shared CSS into the current Streamlit page."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)


def score_badge_html(score: float, label: str) -> str:
    """Return an HTML score badge appropriate to the score level."""
    if score >= 75:
        css = "score-badge-strong"
    elif score >= 50:
        css = "score-badge-moderate"
    elif score >= 25:
        css = "score-badge-limited"
    else:
        css = "score-badge-review"
    return f'<span class="score-badge {css}">{score:.0f} — {label}</span>'


def score_bar_html(score: float) -> str:
    """Return a styled progress bar HTML for a 0-100 score."""
    if score >= 75:
        color = "#22c55e"
    elif score >= 50:
        color = "#f59e0b"
    elif score >= 25:
        color = "#f97316"
    else:
        color = "#ef4444"
    pct = min(100, max(0, score))
    return (
        f'<div class="score-bar-container">'
        f'<div class="score-bar-fill" style="width:{pct}%;background:{color}"></div>'
        f'</div>'
    )


def skill_chips_html(skills: list[str], css_extra: str = "") -> str:
    """Return HTML skill chips."""
    if not skills:
        return "<em style='color:#64748b'>None</em>"
    return " ".join(
        f'<span class="skill-chip {css_extra}">{s}</span>' for s in skills
    )


def alert_html(message: str, kind: str = "info") -> str:
    """Return an HTML alert box."""
    return f'<div class="ira-alert ira-alert-{kind}">{message}</div>'


def page_header(title: str, subtitle: str = "") -> None:
    """Render a standardised page header."""
    import streamlit as st
    sub = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="page-header">'
        f'<h1 class="page-title">{title}</h1>{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


def metric_card(title: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="ira-card-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="ira-card">'
        f'<div class="ira-card-title">{title}</div>'
        f'<div class="ira-card-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )
