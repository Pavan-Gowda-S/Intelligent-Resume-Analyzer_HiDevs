"""
Report generation: HTML and PDF candidate analysis reports, plus CSV export.

HTML is escaped to prevent injection from untrusted resume text.
PDF is generated via ReportLab.  CSV is generated with the standard library.
"""

from __future__ import annotations

import csv
import html
import io
import logging
import re
from datetime import datetime
from pathlib import Path

from src.config import REPORTS_DIR, REPORT_DATE_FORMAT
from src.models import CandidateAnalysis, JobDescription
from src.utils import now_formatted
from src.validators import sanitize_filename

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text), quote=True)


def _score_color(score: float) -> str:
    if score >= 75:
        return "#22c55e"   # green
    if score >= 50:
        return "#f59e0b"   # amber
    if score >= 25:
        return "#f97316"   # orange
    return "#ef4444"        # red


def _report_filename(candidate_name: str, job_title: str, ext: str) -> str:
    safe_name = sanitize_filename(candidate_name or "unknown")
    safe_job = sanitize_filename(job_title or "job")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"report_{safe_name}_{safe_job}_{ts}.{ext}"


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Candidate Analysis Report — {candidate_name}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc;
            color: #1e293b; margin: 0; padding: 0; }}
    .container {{ max-width: 900px; margin: 40px auto; background: #fff;
                  border-radius: 12px; box-shadow: 0 4px 24px #0001;
                  padding: 40px 48px; }}
    h1 {{ font-size: 1.8rem; color: #1e3a5f; border-bottom: 2px solid #e2e8f0;
          padding-bottom: 12px; }}
    h2 {{ font-size: 1.15rem; color: #334155; margin-top: 28px;
          border-left: 4px solid #3b82f6; padding-left: 10px; }}
    .score-badge {{ display: inline-block; background: {score_color};
                    color: #fff; font-size: 2rem; font-weight: 700;
                    padding: 8px 24px; border-radius: 8px; margin: 16px 0; }}
    .label {{ display: inline-block; background: #e0f2fe; color: #0369a1;
               padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;
               margin-left: 12px; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    th {{ background: #f1f5f9; text-align: left; padding: 8px 12px;
          font-size: 0.85rem; color: #64748b; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-size: 0.92rem; }}
    .chip {{ display: inline-block; background: #dbeafe; color: #1d4ed8;
              padding: 2px 10px; border-radius: 12px; font-size: 0.82rem;
              margin: 2px; }}
    .chip.missing {{ background: #fee2e2; color: #dc2626; }}
    .chip.ok {{ background: #dcfce7; color: #16a34a; }}
    .warning {{ background: #fef9c3; border-left: 4px solid #ca8a04;
                padding: 10px 14px; border-radius: 6px; margin: 8px 0;
                font-size: 0.88rem; color: #713f12; }}
    .disclaimer {{ font-size: 0.82rem; color: #94a3b8; margin-top: 32px;
                   border-top: 1px solid #e2e8f0; padding-top: 16px; }}
    .meta {{ color: #64748b; font-size: 0.88rem; margin-bottom: 8px; }}
    pre {{ background: #f1f5f9; padding: 12px; border-radius: 6px;
           white-space: pre-wrap; font-size: 0.82rem; max-height: 300px;
           overflow-y: auto; }}
  </style>
</head>
<body>
<div class="container">
  <h1>Candidate Analysis Report</h1>
  <p class="meta">Generated: {generated_at} &nbsp;|&nbsp; Job: <strong>{job_title}</strong></p>

  <h2>Candidate Information</h2>
  <table>
    <tr><th>Name</th><td>{candidate_name}</td></tr>
    <tr><th>Email</th><td>{email}</td></tr>
    <tr><th>Phone</th><td>{phone}</td></tr>
    <tr><th>File</th><td>{filename}</td></tr>
  </table>

  <h2>Overall Score</h2>
  <div>
    <span class="score-badge" style="background:{score_color}">{total_score:.0f} / 100</span>
    <span class="label">{alignment_label}</span>
  </div>

  <h2>Score Breakdown</h2>
  <table>
    <tr><th>Component</th><th>Score</th><th>Max</th></tr>
    <tr><td>Required Skills</td><td>{req_score:.1f}</td><td>50</td></tr>
    <tr><td>Preferred Skills</td><td>{pref_score:.1f}</td><td>20</td></tr>
    <tr><td>Experience</td><td>{exp_score:.1f}</td><td>20</td></tr>
    <tr><td>Keyword Alignment</td><td>{kw_score:.1f}</td><td>10</td></tr>
    <tr><td><strong>Total</strong></td><td><strong>{total_score:.1f}</strong></td><td><strong>100</strong></td></tr>
  </table>

  <h2>Required Skills</h2>
  <p><strong>Matched:</strong> {matched_required_chips}</p>
  <p><strong>Missing:</strong> {missing_required_chips}</p>

  <h2>Preferred Skills</h2>
  <p><strong>Matched:</strong> {matched_preferred_chips}</p>
  <p><strong>Missing:</strong> {missing_preferred_chips}</p>

  <h2>Experience</h2>
  <p>{experience_text}</p>

  <h2>Education</h2>
  <p>{education_summary}</p>

  <h2>Certifications</h2>
  <p>{certifications_text}</p>

  <h2>Explanation</h2>
  <pre>{explanation}</pre>

  {warnings_block}

  <div class="disclaimer">
    <strong>Disclaimer:</strong> This report is generated automatically by the
    Intelligent Resume Analyzer. It is a screening aid based on text matching
    only. All information must be independently verified. This report must not
    be used as the sole basis for any hiring decision. No protected personal
    attributes were used in scoring.
  </div>
</div>
</body>
</html>"""


def _chips(skills: list[str], css_class: str) -> str:
    if not skills:
        return "<em>None</em>"
    return " ".join(f'<span class="chip {css_class}">{_esc(s)}</span>' for s in skills)


def generate_html_report(
    analysis: CandidateAnalysis,
    job: JobDescription | None = None,
    save_to_disk: bool = True,
) -> str:
    """
    Generate an HTML report for a single candidate analysis.

    Returns the HTML string.  If *save_to_disk* is True, saves the file and
    updates analysis.report_html_path.
    """
    bd = analysis.score_breakdown

    warnings_html = ""
    if bd.data_quality_warnings:
        items = "".join(f"<div class='warning'>⚠ {_esc(w)}</div>" for w in bd.data_quality_warnings)
        warnings_html = f"<h2>Data Quality Warnings</h2>{items}"

    exp_text = "Unknown — employment dates could not be reliably parsed."
    if bd.experience_years_found is not None:
        req_str = (
            f"  (Job requires: {bd.experience_years_required:.1f} yrs)"
            if bd.experience_years_required
            else ""
        )
        exp_text = f"Estimated: {bd.experience_years_found:.1f} years.{req_str}"

    cert_text = ", ".join(_esc(c) for c in analysis.certifications) or "None detected"

    html_content = _HTML_TEMPLATE.format(
        candidate_name=_esc(analysis.candidate_name or "Name not detected"),
        generated_at=_esc(now_formatted()),
        job_title=_esc(analysis.job_title),
        email=_esc(analysis.email or "—"),
        phone=_esc(analysis.phone or "—"),
        filename=_esc(analysis.filename),
        total_score=bd.total_score,
        alignment_label=_esc(bd.alignment_label),
        score_color=_score_color(bd.total_score),
        req_score=bd.required_skills_score,
        pref_score=bd.preferred_skills_score,
        exp_score=bd.experience_score,
        kw_score=bd.keyword_score,
        matched_required_chips=_chips(bd.matched_required, "ok"),
        missing_required_chips=_chips(bd.missing_required, "missing"),
        matched_preferred_chips=_chips(bd.matched_preferred, "ok"),
        missing_preferred_chips=_chips(bd.missing_preferred, "missing"),
        experience_text=_esc(exp_text),
        education_summary=_esc(analysis.education_summary or "Not detected"),
        certifications_text=cert_text,
        explanation=_esc(bd.explanation),
        warnings_block=warnings_html,
    )

    if save_to_disk:
        fname = _report_filename(analysis.candidate_name, analysis.job_title, "html")
        fpath = REPORTS_DIR / fname
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            fpath.write_text(html_content, encoding="utf-8")
            analysis.report_html_path = str(fpath)
        except OSError as exc:
            logger.warning("Could not save HTML report: %s", exc)

    return html_content


# ---------------------------------------------------------------------------
# PDF report via ReportLab
# ---------------------------------------------------------------------------

def generate_pdf_report(
    analysis: CandidateAnalysis,
    save_to_disk: bool = True,
) -> bytes:
    """
    Generate a PDF report and return its bytes.

    Falls back gracefully if ReportLab is unavailable.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
        from reportlab.lib.enums import TA_LEFT
    except ImportError:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")

    bd = analysis.score_breakdown
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    h1 = styles["h1"]
    h2 = styles["h2"]
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=8, textColor=colors.grey)
    body = ParagraphStyle("body", parent=normal, fontSize=10, leading=14)

    story = []

    story.append(Paragraph("Candidate Analysis Report", h1))
    story.append(Paragraph(
        f"Generated: {now_formatted()}  |  Job: {analysis.job_title}", small
    ))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Candidate", h2))
    cand_data = [
        ["Name", analysis.candidate_name or "Not detected"],
        ["Email", analysis.email or "—"],
        ["Phone", analysis.phone or "—"],
        ["File", analysis.filename],
    ]
    t = Table(cand_data, colWidths=[45 * mm, 130 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Overall Score", h2))
    score_data = [
        [f"Score: {bd.total_score:.0f} / 100", bd.alignment_label],
    ]
    ts = Table(score_data, colWidths=[80 * mm, 95 * mm])
    ts.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 18),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(_score_color(bd.total_score))),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#0369a1")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ts)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Score Breakdown", h2))
    breakdown_data = [
        ["Component", "Score", "Max"],
        ["Required Skills", f"{bd.required_skills_score:.1f}", "50"],
        ["Preferred Skills", f"{bd.preferred_skills_score:.1f}", "20"],
        ["Experience", f"{bd.experience_score:.1f}", "20"],
        ["Keyword Alignment", f"{bd.keyword_score:.1f}", "10"],
        ["TOTAL", f"{bd.total_score:.1f}", "100"],
    ]
    bt = Table(breakdown_data, colWidths=[100 * mm, 40 * mm, 35 * mm])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(bt)
    story.append(Spacer(1, 4 * mm))

    def _skill_para(label: str, skills: list[str]) -> None:
        if skills:
            story.append(Paragraph(f"<b>{label}:</b> {', '.join(skills)}", body))
        else:
            story.append(Paragraph(f"<b>{label}:</b> None", body))

    story.append(Paragraph("Skills", h2))
    _skill_para("Required — Matched", bd.matched_required)
    _skill_para("Required — Missing", bd.missing_required)
    _skill_para("Preferred — Matched", bd.matched_preferred)
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Experience", h2))
    if bd.experience_unknown:
        story.append(Paragraph("Could not be reliably determined.", body))
    elif bd.experience_years_found is not None:
        story.append(Paragraph(
            f"Estimated: {bd.experience_years_found:.1f} years  "
            f"(Job requires: {bd.experience_years_required or 'Not specified'})", body
        ))

    story.append(Paragraph("Education", h2))
    story.append(Paragraph(analysis.education_summary or "Not detected", body))

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Explanation", h2))
    for line in bd.explanation.splitlines():
        story.append(Paragraph(line or "&nbsp;", body))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Disclaimer: This report is a screening aid only. "
        "All information must be independently verified. "
        "This report must not be the sole basis for any hiring decision. "
        "No protected personal attributes were used in scoring.",
        small,
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if save_to_disk:
        fname = _report_filename(analysis.candidate_name, analysis.job_title, "pdf")
        fpath = REPORTS_DIR / fname
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            fpath.write_bytes(pdf_bytes)
            analysis.report_pdf_path = str(fpath)
        except OSError as exc:
            logger.warning("Could not save PDF report: %s", exc)

    return pdf_bytes


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def generate_csv_export(analyses: list[CandidateAnalysis]) -> str:
    """Return a CSV string comparing multiple candidate analyses."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Candidate Name", "Filename", "Job Title",
        "Total Score", "Alignment Label",
        "Required Skills Score", "Preferred Skills Score",
        "Experience Score", "Keyword Score",
        "Matched Required Skills", "Missing Required Skills",
        "Matched Preferred Skills",
        "Experience Estimated (yrs)", "Experience Required (yrs)",
        "Experience Unknown",
        "Email", "Phone",
        "Skills",
        "Certifications",
        "Education",
        "Warnings",
        "Analyzed At",
    ]
    writer.writerow(headers)

    for a in analyses:
        bd = a.score_breakdown
        writer.writerow([
            a.candidate_name or "Name not detected",
            a.filename,
            a.job_title,
            f"{bd.total_score:.1f}",
            bd.alignment_label,
            f"{bd.required_skills_score:.1f}",
            f"{bd.preferred_skills_score:.1f}",
            f"{bd.experience_score:.1f}",
            f"{bd.keyword_score:.1f}",
            "; ".join(bd.matched_required),
            "; ".join(bd.missing_required),
            "; ".join(bd.matched_preferred),
            f"{bd.experience_years_found:.1f}" if bd.experience_years_found is not None else "Unknown",
            f"{bd.experience_years_required:.1f}" if bd.experience_years_required else "Not specified",
            "Yes" if bd.experience_unknown else "No",
            a.email or "",
            a.phone or "",
            "; ".join(a.skills),
            "; ".join(a.certifications),
            a.education_summary or "",
            "; ".join(a.warnings),
            a.analyzed_at,
        ])

    return output.getvalue()
