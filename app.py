"""
Intelligent Resume Analyzer — Main Streamlit Application

Run with:
    python -m streamlit run app.py
"""

from __future__ import annotations

import io
import sys
import logging
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Intelligent Resume Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports (after page config)
# ---------------------------------------------------------------------------
from components.styles import inject_css, page_header, alert_html, score_badge_html
from components.dashboard import render_dashboard
from components.candidate_cards import render_candidate_table, render_candidate_detail
from components.visualizations import render_skills_gap_chart

from src.config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB, SAMPLE_DATA_DIR
from src.models import (
    AnalysisSession, CandidateAnalysis, JobDescription, ScoreBreakdown,
)
from src.resume_parser import parse_resume
from src.job_analyzer import analyze_job_description
from src.matching_engine import score_candidate
from src.report_generator import (
    generate_html_report,
    generate_pdf_report,
    generate_csv_export,
)
from src.json_storage import (
    save_job, load_jobs, get_job, delete_job,
    save_candidate_analysis, load_candidate_analyses,
    get_candidate_analysis, delete_candidate_analysis,
    get_analyses_for_session,
    save_session, load_sessions, delete_session,
    clear_all_data, clear_all,
)
from src.validators import (
    validate_file_extension,
    validate_file_size,
    validate_job_title,
    validate_job_description,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inject CSS
# ---------------------------------------------------------------------------
inject_css()

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "page": "Dashboard",
        "selected_candidate_id": None,
        "current_session_analyses": [],
        "last_session_id": None,
        "confirm_delete_job": None,
        "confirm_delete_session": None,
        "confirm_clear_all": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:16px 0 8px 0'>"
        "<div style='font-size:1.5rem;font-weight:800;color:#93c5fd;letter-spacing:0.02em'>"
        "🧠 Resume Analyzer</div>"
        "<div style='font-size:0.75rem;color:#64748b;margin-top:2px'>v1.0 — Local & Offline</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:#1e3a5f;margin:8px 0'>", unsafe_allow_html=True)

    PAGES = [
        "Dashboard",
        "Analyze Resumes",
        "Candidate Details",
        "Job Management",
        "Reports & History",
        "Settings & Help",
    ]
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.session_state["page"] = page

    st.markdown("<hr style='border-color:#1e3a5f;margin:12px 0'>", unsafe_allow_html=True)

    # Sample data loader
    st.markdown(
        "<div style='font-size:0.78rem;color:#64748b;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.06em;margin-bottom:6px'>Demo</div>",
        unsafe_allow_html=True,
    )
    if st.button("📂 Load Sample Data", use_container_width=True):
        st.session_state["_load_sample"] = True


# ---------------------------------------------------------------------------
# Sample data loader helper
# ---------------------------------------------------------------------------
def _load_sample_data() -> None:
    """Parse and analyse all sample resumes against the sample job."""
    sample_dir = SAMPLE_DATA_DIR
    jd_path = sample_dir / "sample_job_description.txt"
    resume_paths = sorted(sample_dir.glob("sample_resume_*.txt"))

    if not jd_path.exists() or not resume_paths:
        st.error("Sample data files not found. Please check the sample_data/ directory.")
        return

    job_text = jd_path.read_text(encoding="utf-8")
    job = analyze_job_description(
        title="Senior Python Developer (Sample)",
        description=job_text,
    )
    save_job(job)

    session = AnalysisSession(job_id=job.id, job_title=job.title)
    analyses: list[CandidateAnalysis] = []

    for rpath in resume_paths:
        file_bytes = rpath.read_bytes()
        resume = parse_resume(file_bytes, rpath.name)
        bd = score_candidate(resume, job)

        edu_lines = [e.raw_text for e in resume.education if e.raw_text]
        edu_summary = "; ".join(edu_lines[:3]) if edu_lines else ""

        analysis = CandidateAnalysis(
            session_id=session.id,
            job_id=job.id,
            job_title=job.title,
            resume_id=resume.id,
            filename=resume.filename,
            candidate_name=resume.candidate_name,
            score_breakdown=bd,
            email=resume.email,
            phone=resume.phone,
            skills=resume.skills,
            education_summary=edu_summary,
            certifications=resume.certifications,
            experience_summary=str(resume.work_experience[0].raw_text)[:200] if resume.work_experience else "",
            warnings=resume.warnings,
        )
        try:
            generate_html_report(analysis, job, save_to_disk=True)
        except Exception as exc:
            logger.warning("HTML report failed for sample: %s", exc)
        save_candidate_analysis(analysis)
        analyses.append(analysis)
        session.candidate_ids.append(analysis.id)

    if analyses:
        session.total_candidates = len(analyses)
        session.avg_score = round(
            sum(a.score_breakdown.total_score for a in analyses) / len(analyses), 1
        )
    save_session(session)
    st.session_state["current_session_analyses"] = analyses
    st.session_state["last_session_id"] = session.id
    st.success(
        f"✅ Sample data loaded! {len(analyses)} candidates analysed against "
        f"'{job.title}'. Go to Candidate Details or Reports & History to explore."
    )


# Handle deferred sample load (must be outside button callback)
if st.session_state.get("_load_sample"):
    st.session_state["_load_sample"] = False
    with st.spinner("Loading sample data…"):
        _load_sample_data()


# ===========================================================================
# PAGE: Dashboard
# ===========================================================================
if page == "Dashboard":
    render_dashboard()


# ===========================================================================
# PAGE: Analyze Resumes
# ===========================================================================
elif page == "Analyze Resumes":
    page_header(
        "Analyze Resumes",
        "Upload resumes and match them against a job description.",
    )

    with st.form("analysis_form"):
        st.subheader("Job Requirements")
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title *", placeholder="e.g. Senior Python Developer")
        with col2:
            min_exp = st.number_input(
                "Min. Experience (years, optional)",
                min_value=0.0, max_value=40.0, value=0.0, step=0.5,
            )

        jd_text = st.text_area(
            "Job Description *",
            height=160,
            placeholder="Paste the full job description here…",
        )

        col3, col4 = st.columns(2)
        with col3:
            req_skills_raw = st.text_input(
                "Required Skills (comma-separated)",
                placeholder="Python, SQL, REST APIs",
            )
        with col4:
            pref_skills_raw = st.text_input(
                "Preferred Skills (comma-separated)",
                placeholder="Docker, AWS, React",
            )

        st.subheader("Upload Resumes")
        uploaded_files = st.file_uploader(
            f"Upload PDF, DOCX, or TXT (max {MAX_FILE_SIZE_MB} MB each)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )

        # Saved job selector
        saved_jobs = load_jobs()
        if saved_jobs:
            st.markdown("**Or load a saved job description:**")
            job_options = {f"{j.title} ({j.id[:8]})": j for j in saved_jobs}
            chosen_job_label = st.selectbox(
                "Saved Jobs", ["— select —"] + list(job_options.keys()),
                label_visibility="collapsed",
            )
        else:
            chosen_job_label = "— select —"
            job_options = {}

        submit = st.form_submit_button("🔍 Analyze Resumes", use_container_width=True)

    if submit:
        # Validate inputs
        errors: list[str] = []

        # Load from saved job if selected
        if chosen_job_label != "— select —" and chosen_job_label in job_options:
            saved_job = job_options[chosen_job_label]
            if not job_title.strip():
                job_title = saved_job.title
            if not jd_text.strip():
                jd_text = saved_job.description
            if not req_skills_raw.strip():
                req_skills_raw = ", ".join(saved_job.required_skills)
            if not pref_skills_raw.strip():
                pref_skills_raw = ", ".join(saved_job.preferred_skills)

        ok, msg = validate_job_title(job_title)
        if not ok:
            errors.append(msg)
        ok, msg = validate_job_description(jd_text)
        if not ok:
            errors.append(msg)
        if not uploaded_files:
            errors.append("Please upload at least one resume file.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            req_skills = [s.strip() for s in req_skills_raw.split(",") if s.strip()]
            pref_skills = [s.strip() for s in pref_skills_raw.split(",") if s.strip()]
            min_exp_val = float(min_exp) if min_exp > 0 else None

            # Build job
            job = analyze_job_description(
                title=job_title,
                description=jd_text,
                required_skills=req_skills or None,
                preferred_skills=pref_skills or None,
                min_experience_years=min_exp_val,
            )
            save_job(job)

            session = AnalysisSession(job_id=job.id, job_title=job.title)
            analyses: list[CandidateAnalysis] = []
            progress = st.progress(0, text="Starting analysis…")

            seen_names: set[str] = set()
            total = len(uploaded_files)

            for i, uploaded_file in enumerate(uploaded_files):
                fname = uploaded_file.name
                progress.progress((i) / total, text=f"Processing {fname}…")

                # Duplicate file check
                if fname in seen_names:
                    st.warning(f"Duplicate file skipped: {fname}")
                    continue
                seen_names.add(fname)

                file_bytes = uploaded_file.read()

                # Size validation
                ok_size, size_msg = validate_file_size(file_bytes, fname)
                if not ok_size:
                    st.error(size_msg)
                    continue

                # Parse
                try:
                    resume = parse_resume(file_bytes, fname)
                except Exception as exc:
                    st.error(f"Error parsing {fname}: {exc}")
                    logger.exception("Parse error for %s", fname)
                    continue

                if not resume.parse_success:
                    for w in resume.warnings:
                        st.warning(f"{fname}: {w}")
                    continue

                # Score
                bd = score_candidate(resume, job)

                edu_lines = [e.raw_text for e in resume.education if e.raw_text]
                edu_summary = "; ".join(edu_lines[:3]) if edu_lines else ""

                analysis = CandidateAnalysis(
                    session_id=session.id,
                    job_id=job.id,
                    job_title=job.title,
                    resume_id=resume.id,
                    filename=resume.filename,
                    candidate_name=resume.candidate_name,
                    score_breakdown=bd,
                    email=resume.email,
                    phone=resume.phone,
                    skills=resume.skills,
                    education_summary=edu_summary,
                    certifications=resume.certifications,
                    experience_summary=(
                        resume.work_experience[0].raw_text[:200]
                        if resume.work_experience else ""
                    ),
                    warnings=resume.warnings,
                )

                # Generate HTML report
                try:
                    generate_html_report(analysis, job, save_to_disk=True)
                except Exception as exc:
                    logger.warning("HTML report generation failed: %s", exc)
                    st.warning(f"HTML report could not be generated for {fname}.")

                save_candidate_analysis(analysis)
                analyses.append(analysis)
                session.candidate_ids.append(analysis.id)

            progress.progress(1.0, text="Analysis complete.")

            if analyses:
                session.total_candidates = len(analyses)
                session.avg_score = round(
                    sum(a.score_breakdown.total_score for a in analyses) / len(analyses), 1
                )
                save_session(session)
                st.session_state["current_session_analyses"] = analyses
                st.session_state["last_session_id"] = session.id
                st.success(
                    f"✅ Analysed {len(analyses)} candidate(s) for '{job.title}'. "
                    "Results saved. Use **Candidate Details** to explore individual reports."
                )
            else:
                st.error("No resumes were successfully processed. Check file formats and sizes.")

    # Show current session results if available
    current_analyses = st.session_state.get("current_session_analyses", [])
    if current_analyses:
        st.markdown("---")
        st.subheader("Current Session Results")
        selected_id = render_candidate_table(current_analyses)
        if selected_id:
            st.session_state["selected_candidate_id"] = selected_id
            st.session_state["page"] = "Candidate Details"
            st.rerun()


# ===========================================================================
# PAGE: Candidate Details
# ===========================================================================
elif page == "Candidate Details":
    page_header(
        "Candidate Details",
        "Full analysis report for an individual candidate.",
    )

    all_analyses = load_candidate_analyses()
    if not all_analyses:
        st.markdown(
            alert_html("No analyses found. Go to <b>Analyze Resumes</b> first.", "info"),
            unsafe_allow_html=True,
        )
    else:
        # Selector
        options = {
            f"{a.candidate_name or 'Unknown'} — {a.job_title} [{a.id[:8]}]": a.id
            for a in reversed(all_analyses)
        }
        preselect = st.session_state.get("selected_candidate_id")
        preselect_label = next(
            (lbl for lbl, aid in options.items() if aid == preselect), None
        )

        chosen_label = st.selectbox(
            "Select candidate",
            list(options.keys()),
            index=list(options.keys()).index(preselect_label) if preselect_label else 0,
        )
        chosen_id = options[chosen_label]
        analysis = get_candidate_analysis(chosen_id)

        if analysis:
            render_candidate_detail(analysis)

            st.markdown("---")
            st.subheader("Download Report")
            col_html, col_pdf = st.columns(2)

            with col_html:
                try:
                    html_content = generate_html_report(analysis, save_to_disk=True)
                    st.download_button(
                        "⬇ Download HTML Report",
                        data=html_content.encode("utf-8"),
                        file_name=f"report_{analysis.candidate_name or 'candidate'}_{analysis.job_title}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"HTML report generation failed: {exc}")

            with col_pdf:
                try:
                    pdf_bytes = generate_pdf_report(analysis, save_to_disk=True)
                    save_candidate_analysis(analysis)
                    st.download_button(
                        "⬇ Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"report_{analysis.candidate_name or 'candidate'}_{analysis.job_title}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"PDF report generation failed: {exc}")
        else:
            st.error("Could not load the selected analysis.")


# ===========================================================================
# PAGE: Job Management
# ===========================================================================
elif page == "Job Management":
    page_header(
        "Job Management",
        "Create, edit, and delete saved job descriptions.",
    )

    tab_list, tab_create = st.tabs(["Saved Jobs", "Create / Edit Job"])

    with tab_list:
        jobs = load_jobs()
        if not jobs:
            st.markdown(
                alert_html("No jobs saved yet. Use the 'Create / Edit Job' tab to add one.", "info"),
                unsafe_allow_html=True,
            )
        else:
            for job in jobs:
                with st.expander(f"📋 {job.title}  ({job.id[:8]})", expanded=False):
                    st.markdown(f"**Description:** {job.description[:200]}{'…' if len(job.description)>200 else ''}")
                    st.markdown(f"**Required skills:** {', '.join(job.required_skills) or 'None'}")
                    st.markdown(f"**Preferred skills:** {', '.join(job.preferred_skills) or 'None'}")
                    st.markdown(f"**Min. experience:** {job.min_experience_years or 'Not specified'} yrs")
                    st.markdown(f"**Created:** {job.created_at[:10]}")

                    del_col, _ = st.columns([1, 3])
                    with del_col:
                        if st.button("🗑 Delete", key=f"del_job_{job.id}"):
                            st.session_state["confirm_delete_job"] = job.id

                    if st.session_state.get("confirm_delete_job") == job.id:
                        st.warning(f"Are you sure you want to delete **{job.title}**?")
                        c1, c2 = st.columns(2)
                        if c1.button("Yes, delete", key=f"confirm_del_{job.id}"):
                            delete_job(job.id)
                            st.session_state["confirm_delete_job"] = None
                            st.success("Job deleted.")
                            st.rerun()
                        if c2.button("Cancel", key=f"cancel_del_{job.id}"):
                            st.session_state["confirm_delete_job"] = None
                            st.rerun()

    with tab_create:
        st.subheader("Create New Job Description")
        with st.form("create_job_form"):
            title = st.text_input("Job Title *", placeholder="e.g. Data Engineer")
            desc = st.text_area("Job Description *", height=150)
            req = st.text_input("Required Skills (comma-separated)")
            pref = st.text_input("Preferred Skills (comma-separated)")
            min_exp_new = st.number_input("Min. Experience (years)", min_value=0.0, max_value=40.0, value=0.0, step=0.5)
            save_btn = st.form_submit_button("💾 Save Job", use_container_width=True)

        if save_btn:
            errs = []
            ok, msg = validate_job_title(title)
            if not ok:
                errs.append(msg)
            ok, msg = validate_job_description(desc)
            if not ok:
                errs.append(msg)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                req_list = [s.strip() for s in req.split(",") if s.strip()]
                pref_list = [s.strip() for s in pref.split(",") if s.strip()]
                job = analyze_job_description(
                    title=title,
                    description=desc,
                    required_skills=req_list or None,
                    preferred_skills=pref_list or None,
                    min_experience_years=float(min_exp_new) if min_exp_new > 0 else None,
                )
                save_job(job)
                st.success(f"✅ Job '{title}' saved successfully (ID: {job.id[:8]}).")


# ===========================================================================
# PAGE: Reports & History
# ===========================================================================
elif page == "Reports & History":
    page_header(
        "Reports & History",
        "Browse past analysis sessions and download reports.",
    )

    sessions = load_sessions()
    if not sessions:
        st.markdown(
            alert_html("No analysis sessions found. Analyze some resumes first.", "info"),
            unsafe_allow_html=True,
        )
    else:
        sessions_sorted = sorted(sessions, key=lambda s: s.created_at, reverse=True)

        for session in sessions_sorted:
            with st.expander(
                f"🗂 {session.job_title}  |  {session.total_candidates} candidates  |  "
                f"Avg: {session.avg_score:.0f}  |  {session.created_at[:10]}",
                expanded=False,
            ):
                session_analyses = get_analyses_for_session(session.id)

                if session_analyses:
                    # CSV export
                    csv_str = generate_csv_export(session_analyses)
                    st.download_button(
                        "⬇ Export as CSV",
                        data=csv_str.encode("utf-8"),
                        file_name=f"session_{session.id[:8]}_candidates.csv",
                        mime="text/csv",
                    )

                    # Candidate list
                    for a in sorted(session_analyses, key=lambda x: x.score_breakdown.total_score, reverse=True):
                        bd = a.score_breakdown
                        col1, col2, col3, col4 = st.columns([2, 1, 1.5, 1])
                        col1.markdown(f"**{a.candidate_name or 'Unknown'}**  \n{a.filename}")
                        col2.markdown(f"**{bd.total_score:.0f}** / 100")
                        col3.markdown(
                            score_badge_html(bd.total_score, bd.alignment_label),
                            unsafe_allow_html=True,
                        )
                        if col4.button("View", key=f"hist_view_{a.id}"):
                            st.session_state["selected_candidate_id"] = a.id
                            st.session_state["page"] = "Candidate Details"
                            st.rerun()
                else:
                    st.info("No candidate records for this session.")

                # Delete session
                st.markdown("---")
                if st.button("🗑 Delete Session", key=f"del_sess_{session.id}"):
                    st.session_state["confirm_delete_session"] = session.id

                if st.session_state.get("confirm_delete_session") == session.id:
                    st.warning("Delete this session and all associated candidate records?")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, delete", key=f"confirm_sess_{session.id}"):
                        delete_session(session.id)
                        st.session_state["confirm_delete_session"] = None
                        st.success("Session deleted.")
                        st.rerun()
                    if c2.button("Cancel", key=f"cancel_sess_{session.id}"):
                        st.session_state["confirm_delete_session"] = None
                        st.rerun()


# ===========================================================================
# PAGE: Settings & Help
# ===========================================================================
elif page == "Settings & Help":
    page_header("Settings & Help", "Configuration, privacy information, and usage guide.")

    tab_help, tab_settings, tab_privacy = st.tabs(["Help & Usage", "Settings", "Privacy"])

    with tab_help:
        st.subheader("Supported File Formats")
        st.markdown(
            "| Format | Notes |\n"
            "|--------|-------|\n"
            "| **PDF** | Text-based PDFs only. Scanned/image PDFs are detected but not parsed. |\n"
            "| **DOCX** | All paragraph and table text is extracted. |\n"
            "| **TXT** | UTF-8 or latin-1 encoding supported. |\n"
            f"\n**Maximum file size:** {MAX_FILE_SIZE_MB} MB per file."
        )

        st.subheader("How the Matching Score Works")
        st.markdown("""
The overall score (0–100) is calculated from four weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Required Skills | 50 pts | Fraction of required skills found in the resume |
| Preferred Skills | 20 pts | Fraction of preferred skills found |
| Experience | 20 pts | Estimated experience vs. job requirement |
| Keyword Alignment | 10 pts | Important job keywords found in the resume |

**Score labels:**
- **Strong Alignment** — 75 or above
- **Moderate Alignment** — 50–74
- **Limited Alignment** — 25–49
- **Needs Manual Review** — below 25

These labels indicate alignment with stated requirements only.
**They are not hiring decisions or assessments of candidate quality.**
        """)

        st.subheader("Quick Start")
        st.markdown("""
1. Go to **Job Management** and create (or load) a job description.
2. Go to **Analyze Resumes**, fill in the job details, and upload resume files.
3. Click **Analyze Resumes** to run the analysis.
4. Explore individual candidates in **Candidate Details**.
5. Download reports from the candidate detail page.
6. View history and export CSVs from **Reports & History**.
7. Or use **Load Sample Data** in the sidebar to try a ready-made demo.
        """)

        st.subheader("Known Limitations")
        st.markdown("""
- **Scanned PDF files** cannot be parsed. Only text-based PDFs are supported.
- **Name detection** is heuristic and may fail on unusual resume layouts.
- **Experience calculation** requires parseable date ranges and may be unavailable.
- **Skill extraction** uses a predefined taxonomy. Skills not in the taxonomy are not detected.
- The application works entirely offline — no AI or external API is used.
        """)

    with tab_settings:
        st.subheader("Storage Information")
        from src.config import DATA_DIR, REPORTS_DIR
        st.markdown(f"- **Analysis data:** `{DATA_DIR}`")
        st.markdown(f"- **Generated reports:** `{REPORTS_DIR}`")

        st.subheader("Clear Application Data")
        st.warning(
            "⚠️ Clearing data is irreversible. Analysis records and session history "
            "will be permanently deleted. Saved job descriptions can be cleared separately."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Clear Analysis Data Only", use_container_width=True):
                st.session_state["confirm_clear_all"] = "analysis"
        with col_b:
            if st.button("Clear ALL Data (incl. Jobs)", use_container_width=True):
                st.session_state["confirm_clear_all"] = "all"

        if st.session_state.get("confirm_clear_all"):
            action = st.session_state["confirm_clear_all"]
            label = "all analysis data" if action == "analysis" else "ALL data including jobs"
            st.error(f"This will permanently delete {label}. Are you sure?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete permanently"):
                if action == "analysis":
                    clear_all_data()
                else:
                    clear_all()
                st.session_state["confirm_clear_all"] = False
                st.session_state["current_session_analyses"] = []
                st.success("Data cleared.")
                st.rerun()
            if c2.button("Cancel"):
                st.session_state["confirm_clear_all"] = False
                st.rerun()

    with tab_privacy:
        st.subheader("Privacy & Responsible Use")
        st.markdown("""
### How your data is handled

- **All processing is local.** No resume content is sent to any external server or API.
- **Only structured analysis results are stored** (extracted fields, scores, timestamps).
  Raw resume text is processed in-memory and is not persisted to disk.
- **No protected attributes are scored.** Name, email, phone, age, gender, nationality,
  or any other personal characteristic not directly related to the job requirements is
  not used in the match score.

### What the score represents

The match score reflects only textual alignment between a resume and a stated job
description.  It is **not** a prediction of job performance, cultural fit, or any
other quality.  The recruiter must independently verify all extracted information and
make their own judgment.

### Data retention

Analysis records are stored in the `data/` directory as JSON files.  You can delete
individual sessions from **Reports & History** or clear all data from **Settings**.
Generated reports are stored in `reports/` and are not automatically deleted.

### Deletion

Use the Settings tab to clear analysis data, or delete individual sessions from
Reports & History.  Both the `data/` directory and the `reports/` directory are
listed in `.gitignore` to prevent accidental commits of personal information.

### No automated decisions

This application is a **screening aid only**.  It must not be used to automatically
reject candidates or make final hiring decisions.  A qualified human recruiter must
review all results.
        """)
