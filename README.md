# Intelligent Resume Analyzer

A privacy-focused, explainable Python application designed for technical recruiters and hiring managers. It parses resumes in PDF, DOCX, and TXT formats, extracts skills, education, experience, and contact details, and matches candidates against job descriptions using a deterministic, fully explainable scoring algorithm.

The system runs entirely locally and offline, with zero external API dependencies, no mandatory cloud accounts, and no closed-source models.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Problem Statement](#2-problem-statement)
- [3. Key Features](#3-key-features)
- [4. Technology Stack](#4-technology-stack)
- [5. System Architecture & Directory Structure](#5-system-architecture--directory-structure)
- [6. How the Matching Algorithm Works](#6-how-the-matching-algorithm-works)
  - [Scoring Formula](#scoring-formula)
  - [Component Breakdown](#component-breakdown)
  - [Alignment Labels](#alignment-labels)
- [7. Supported File Formats & Known Limitations](#7-supported-file-formats--known-limitations)
- [8. Installation & Setup](#8-installation--setup)
  - [Prerequisites](#prerequisites)
  - [Windows (PowerShell)](#windows-powershell)
  - [macOS and Linux (Bash/Zsh)](#macos-and-linux-bashzsh)
- [9. How to Launch the Application](#9-how-to-launch-the-application)
- [10. Running the Test Suite](#10-running-the-test-suite)
- [11. Sample Data Demonstration](#11-sample-data-demonstration)
- [12. JSON Storage & Data Retention](#12-json-storage--data-retention)
- [13. Privacy, Security & Responsible Use](#13-privacy-security--responsible-use)
- [14. Troubleshooting](#14-troubleshooting)
- [15. Future Roadmap](#15-future-roadmap)

---

## 1. Project Overview

The **Intelligent Resume Analyzer** provides talent acquisition teams with an objective, auditable screening tool. Unlike "black-box" generative AI screeners that may introduce uncontrolled bias, hallucinate qualifications, or violate candidate privacy by sending personal data to external APIs, this tool operates on deterministic, explainable principles:

- Extracts concrete facts (skills, titles, years of experience, degrees).
- Measures alignment with explicit job requirements using transparent arithmetic weights.
- Generates downloadable reports (HTML, PDF) and comparison tables (CSV).
- Keeps candidate data completely on the local workstation.

---

## 2. Problem Statement

Recruiters frequently face high volumes of candidate resumes across varying formats and layouts. Typical screening workflows suffer from:

1. **Unconscious Bias & Inconsistency:** Manual initial passes can vary based on fatigue, order of reading, or personal biases.
2. **Black-Box AI Risks:** Third-party generative LLMs often hallucinate competencies, unpredictably penalize valid phrasing, and lack transparency for regulatory audits (e.g., EU AI Act, NYC Local Law 144).
3. **Privacy Vulnerabilities:** Transmitting resumes—which contain full names, addresses, emails, phone numbers, and employment histories—to cloud AI APIs presents serious compliance risks under GDPR, CCPA, and enterprise confidentiality rules.
4. **Lack of Explainability:** Candidates and hiring managers rarely receive clear, itemized reasons why a resume was ranked or filtered.

This application directly addresses these challenges by computing explainable, auditable alignment scores strictly locally.

---

## 3. Key Features

- **Multi-Format In-Memory Parsing:** Parses `.pdf` (using PyMuPDF), `.docx` (using python-docx), and `.txt` files in memory without saving raw documents to disk.
- **Scanned Document Detection:** Flags image-only/scanned PDFs with user-friendly warnings indicating that OCR is unavailable in this offline version.
- **Taxonomy-Driven Skill Extraction:** Comprehensive taxonomy spanning programming languages, web technologies, backend frameworks, databases, machine learning/AI, DevOps tools, and testing methodologies with whole-word regex to eliminate substring false positives (e.g., distinguishing "C" from "access" or "Go" from "going").
- **Smart Contact & Section Extraction:** Heuristically extracts candidate name, email, phone number, work experience history, education records, and certifications.
- **Deterministic 0–100 Matching Engine:** Evaluates candidates across 4 configurable dimensions (Required Skills, Preferred Skills, Experience Duration, Job Keywords).
- **Audit-Ready Score Explanations:** Every candidate evaluation includes an itemized breakdown showing exactly which skills were matched, which are missing, estimated experience, and data-quality warnings.
- **Multi-Candidate Batch Upload:** Upload multiple resumes simultaneously for a single job description; view real-time analysis progress.
- **Job Description Management:** Create, save, edit, and delete job requirements stored in local JSON format.
- **Export & Reporting:**
  - Standalone, styled **HTML reports** with XSS protection.
  - Formatted **PDF reports** generated using ReportLab.
  - Multi-candidate **CSV comparisons** for spreadsheet analysis.
- **Recruiter Dashboard:** Visual distribution charts, metric summaries, and session histories powered by local data.
- **Built-in Synthetic Demo Data:** Instant 1-click sample dataset demonstrating strong, moderate, and limited candidate alignments.

---

## 4. Technology Stack

- **Language:** Python 3.11+ (fully compatible with Python 3.11, 3.12, 3.13, 3.14)
- **Frontend / UI:** Streamlit with custom dark-themed CSS
- **PDF Extraction:** PyMuPDF (`fitz`) with automatic fallback to `pdfminer.six`
- **DOCX Extraction:** `python-docx`
- **Text & Date Processing:** Python Standard Library (`re`, `unicodedata`, `io`) + `python-dateutil`
- **Report Generation:** `reportlab` (PDF generation) and HTML5/CSS template engine
- **Data Persistence:** Local atomic JSON storage (`json`, `tempfile`, `os.replace`)
- **Testing:** `pytest` (116 unit and integration tests)

---

## 5. System Architecture & Directory Structure

The project strictly decouples presentation logic, domain processing, data models, and persistence:

```
Intelligent-Resume-Analyzer_HiDevs/
├── app.py                      # Main Streamlit application and page router
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation
├── .gitignore                  # Git exclusions for data, virtual environments, and caches
│
├── src/                        # Core backend package
│   ├── __init__.py
│   ├── config.py               # Constants, scoring weights, file constraints, paths
│   ├── models.py               # Dataclass models (ParsedResume, JobDescription, etc.)
│   ├── validators.py           # File extension, size, and input validation
│   ├── utils.py                # Text normalization, date math, scoring helpers
│   ├── skill_extractor.py      # Skill taxonomy & regex whole-word matcher
│   ├── text_processor.py       # Section segmenter, name/email/phone extractors
│   ├── resume_parser.py        # PDF, DOCX, and TXT parsing pipeline
│   ├── job_analyzer.py         # Job description parser & requirement extractor
│   ├── matching_engine.py      # Explainable scoring engine (0-100 score + explanation)
│   ├── json_storage.py         # Atomic JSON persistence layer (CRUD operations)
│   └── report_generator.py     # HTML, PDF (ReportLab), and CSV report builders
│
├── components/                 # Reusable Streamlit UI components
│   ├── __init__.py
│   ├── styles.py               # Custom CSS themes, score badges, cards, alerts
│   ├── dashboard.py            # Dashboard view with metrics & distribution charts
│   ├── candidate_cards.py      # Candidate summary tables, cards, & detail viewer
│   └── visualizations.py       # Progress gauges, skill-gap charts, distribution plots
│
├── sample_data/                # Synthetic demonstration files (fictional records)
│   ├── sample_job_description.txt
│   ├── sample_resume_1.txt     # Strong alignment demonstration
│   ├── sample_resume_2.txt     # Moderate alignment demonstration
│   └── sample_resume_3.txt     # Limited alignment / unverifiable experience
│
├── tests/                      # Automated test suite (pytest)
│   ├── __init__.py
│   ├── test_validators.py      # Input validation tests
│   ├── test_skill_extractor.py # Taxonomy, alias, and false-positive tests
│   ├── test_resume_parser.py   # PDF, DOCX, TXT parser tests
│   ├── test_job_analyzer.py    # Job requirement extraction tests
│   ├── test_matching_engine.py # Deterministic scoring & edge-case tests
│   ├── test_json_storage.py    # Persistence, recovery, & cascade delete tests
│   └── test_report_generator.py# HTML, PDF, CSV, and XSS safety tests
│
├── data/                       # Local JSON storage directory (ignored in git)
│   └── .gitkeep
└── reports/                    # Generated downloadable reports (ignored in git)
    └── .gitkeep
```

---

## 6. How the Matching Algorithm Works

The scoring algorithm is **deterministic**, **transparent**, and **configurable**.

### Scoring Formula

The total match score is calculated out of **100 points**:

$$\text{Total Score} = S_{\text{required}} + S_{\text{preferred}} + S_{\text{experience}} + S_{\text{keywords}}$$

Where:
- $S_{\text{required}} = \left(\frac{\text{Matched Required Skills}}{\text{Total Required Skills}}\right) \times 50$
- $S_{\text{preferred}} = \left(\frac{\text{Matched Preferred Skills}}{\text{Total Preferred Skills}}\right) \times 20$
- $S_{\text{experience}} = \min\left(1.0, \frac{\text{Candidate Years}}{\text{Required Years}}\right) \times 20$
- $S_{\text{keywords}} = \left(\frac{\text{Matched Keywords}}{\text{Top Job Keywords}}\right) \times 10$

### Component Breakdown

1. **Required Skills (50 Points):** Measures the fraction of mandatory skills identified in the resume. If no required skills are specified by the recruiter, this component awards full marks with a transparent warning.
2. **Preferred Skills (20 Points):** Rewards optional qualifications. If no preferred skills are listed, full marks are awarded to prevent penalizing candidates.
3. **Experience Duration (20 Points):** Compares estimated employment duration against the requirement. If dates are unclear or missing, the system assigns a neutral 50% fraction ($10 / 20\text{ points}$) and tags the record with an explicit warning for human review.
4. **Keywords & Responsibilities (10 Points):** Assesses broader domain terminology overlap using tokenized keyword analysis with stopwords excluded.

### Alignment Labels

Candidates receive a clear alignment tier:
- **Strong Alignment** ($\ge 75$): Meets nearly all required skills and experience benchmarks.
- **Moderate Alignment** ($50 - 74$): Substantial overlap; may be missing select preferred skills or years of experience.
- **Limited Alignment** ($25 - 49$): Significant skill gaps; requires further screening.
- **Needs Manual Review** ($< 25$ or missing critical data): Major gaps or parsing ambiguities.

> **Important:** Alignment labels are screening aids, not automated hiring decisions.

---

## 7. Supported File Formats & Known Limitations

| Format | Parsing Engine | Capabilities & Known Limitations |
| :--- | :--- | :--- |
| **PDF (`.pdf`)** | PyMuPDF (`fitz`) / `pdfminer.six` | Extracts digital text streams. Detects scanned/image-only PDFs and warns the recruiter rather than generating silent empty matches. (OCR is intentionally omitted in this lightweight local version.) |
| **DOCX (`.docx`)** | `python-docx` | Extracts paragraph bodies and internal tabular content. |
| **TXT (`.txt`)** | Native multi-encoding | Handles UTF-8, UTF-16, Latin-1, and CP1252 encodings. |

**General Limitations:**
- Unconventional multi-column layouts or creative graphics may alter line ordering.
- Experience calculations rely on identifiable month/year ranges.
- Highly unusual name placement may trigger a "Name not detected" notification, prompting manual verification.

---

## 8. Installation & Setup

### Prerequisites

- Python 3.11 or newer installed on your system.
- Git installed.

### Windows (PowerShell)

```powershell
# 1. Clone repository (if not already inside project directory)
git clone https://github.com/Pavan-Gowda-S/Intelligent-Resume-Analyzer_HiDevs.git
cd Intelligent-Resume-Analyzer_HiDevs

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS and Linux (Bash/Zsh)

```bash
# 1. Clone repository (if not already inside project directory)
git clone https://github.com/Pavan-Gowda-S/Intelligent-Resume-Analyzer_HiDevs.git
cd Intelligent-Resume-Analyzer_HiDevs

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Upgrade pip and install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

## 9. How to Launch the Application

Make sure your virtual environment is activated, then run:

```bash
python -m streamlit run app.py
```

The Streamlit server will start and open in your default browser at `http://localhost:8501`.

---

## 10. Running the Test Suite

The test suite covers validators, skill extraction, regex false-positive safeguards, PDF/DOCX/TXT parsers, matching formulas, JSON persistence, and report generation.

Run all tests with:

```bash
python -m pytest tests/ -v
```

Expected output:
```text
============================= 116 passed in 1.21s =============================
```

---

## 11. Sample Data Demonstration

The repository includes pre-built synthetic demonstration data in `sample_data/`:

1. Launch the app (`python -m streamlit run app.py`).
2. In the left sidebar, click the **📂 Load Sample Data** button under the **Demo** heading.
3. The app will automatically:
   - Create a sample job description: *"Senior Python Developer"*.
   - Parse all three synthetic candidate resumes.
   - Run matching calculations and display results on the **Dashboard** and **Candidate Details** pages.
4. **Candidate outcomes:**
   - **Jordan Mitchell** (`sample_resume_1.txt`): ~82 Score — *Strong Alignment*.
   - **Alex Rivera** (`sample_resume_2.txt`): ~58 Score — *Moderate Alignment*.
   - **Morgan Chen** (`sample_resume_3.txt`): ~42 Score — *Limited Alignment* with unknown experience warning.

---

## 12. JSON Storage & Data Retention

- **Structured Storage:** Jobs, candidate analyses, and session histories are stored in `data/jobs.json`, `data/candidates.json`, and `data/sessions.json`.
- **Atomic Operations:** Writes use temporary files and atomic file replacement (`os.replace`) to prevent corrupted states if a write is interrupted.
- **Data Deletion:**
  - Individual jobs can be removed under **Job Management**.
  - Individual analysis sessions can be deleted under **Reports & History**.
  - All application data can be cleared under **Settings & Help -> Clear Application Data**.
- **Git Exclusions:** The `data/*.json` and `reports/*` directories are included in `.gitignore` to prevent committing candidate records or proprietary job descriptions.

---

## 13. Privacy, Security & Responsible Use

1. **Local Execution:** 100% of resume processing occurs in memory on the host computer. No telemetry or resume data is sent over the internet.
2. **No Protected Attributes Used:** Demographic factors—including candidate name, gender, race, age, religion, phone number, physical address, and photos—are strictly excluded from scoring features.
3. **No Automated Decisions:** The tool functions solely as an initial screening assistant. It does not automatically reject candidates. Final hiring evaluations must be conducted by human recruiters.
4. **Sanitized Output:** All user-supplied inputs and extracted resume fields are escaped (`html.escape`) during report generation to defend against Cross-Site Scripting (XSS).

---

## 14. Troubleshooting

- **`ModuleNotFoundError: No module named 'streamlit'` (or other package):**
  Ensure your virtual environment is active (`.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on macOS/Linux), then run `pip install -r requirements.txt`.
- **Scanned PDF warning:**
  The PDF is image-based. Scanned PDFs require an OCR engine. For this version, request a text-based PDF, DOCX, or TXT version of the candidate's resume.
- **Port 8501 is in use:**
  Run `python -m streamlit run app.py --server.port 8502`.

---

## 15. Future Roadmap

- Optional local OCR support using Tesseract for scanned PDFs.
- Custom recruiter taxonomy editor inside the Settings UI.
- Multi-language resume parsing support.
- Configurable scoring weight presets (e.g., Senior vs. Junior hiring weights).

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
