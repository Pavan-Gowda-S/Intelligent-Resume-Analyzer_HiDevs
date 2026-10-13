"""
Skill taxonomy and extraction.

The taxonomy is defined as a list of (canonical_name, category, [aliases])
tuples.  Matching is whole-word aware and case-insensitive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Taxonomy definition
# ---------------------------------------------------------------------------

_RAW_TAXONOMY: list[tuple[str, str, list[str]]] = [
    # Programming languages
    ("Python", "Programming Languages", ["python3", "py"]),
    ("Java", "Programming Languages", []),
    ("JavaScript", "Programming Languages", ["js", "ecmascript"]),
    ("TypeScript", "Programming Languages", ["ts"]),
    ("C++", "Programming Languages", ["cpp", "c plus plus"]),
    ("C#", "Programming Languages", ["csharp", "c sharp"]),
    ("C", "Programming Languages", []),          # matched with word boundary only
    ("Go", "Programming Languages", ["golang"]),
    ("Rust", "Programming Languages", []),
    ("Ruby", "Programming Languages", []),
    ("PHP", "Programming Languages", []),
    ("Swift", "Programming Languages", []),
    ("Kotlin", "Programming Languages", []),
    ("R", "Programming Languages", []),
    ("Scala", "Programming Languages", []),
    ("MATLAB", "Programming Languages", ["matlab"]),
    ("Shell", "Programming Languages", ["bash", "sh", "shell scripting", "zsh"]),
    ("PowerShell", "Programming Languages", []),

    # Web frontend
    ("HTML", "Web Technologies", ["html5"]),
    ("CSS", "Web Technologies", ["css3", "stylesheets"]),
    ("React", "Web Technologies", ["reactjs", "react.js"]),
    ("Vue.js", "Web Technologies", ["vuejs", "vue"]),
    ("Angular", "Web Technologies", ["angularjs"]),
    ("Next.js", "Web Technologies", ["nextjs"]),
    ("Node.js", "Web Technologies", ["nodejs", "node"]),
    ("jQuery", "Web Technologies", ["jquery"]),
    ("Bootstrap", "Web Technologies", []),
    ("Tailwind CSS", "Web Technologies", ["tailwind"]),
    ("SASS", "Web Technologies", ["scss", "sass"]),
    ("Redux", "Web Technologies", []),
    ("GraphQL", "Web Technologies", []),
    ("WebSockets", "Web Technologies", ["websocket"]),

    # Backend / APIs
    ("REST APIs", "Backend & APIs", ["rest api", "restful", "restful api", "rest"]),
    ("Flask", "Backend & APIs", []),
    ("FastAPI", "Backend & APIs", []),
    ("Django", "Backend & APIs", []),
    ("Spring Boot", "Backend & APIs", ["spring"]),
    ("Express.js", "Backend & APIs", ["express", "expressjs"]),
    ("ASP.NET", "Backend & APIs", ["asp.net core", "asp net"]),
    ("gRPC", "Backend & APIs", ["grpc"]),
    ("Microservices", "Backend & APIs", ["microservice architecture"]),
    ("API Design", "Backend & APIs", ["api development"]),

    # Data & Databases
    ("SQL", "Data & Databases", []),
    ("PostgreSQL", "Data & Databases", ["postgres"]),
    ("MySQL", "Data & Databases", []),
    ("SQLite", "Data & Databases", []),
    ("MongoDB", "Data & Databases", ["mongo"]),
    ("Redis", "Data & Databases", []),
    ("Elasticsearch", "Data & Databases", ["elastic search", "elastic"]),
    ("Cassandra", "Data & Databases", []),
    ("DynamoDB", "Data & Databases", []),
    ("Oracle", "Data & Databases", ["oracle db"]),
    ("pandas", "Data & Databases", []),
    ("NumPy", "Data & Databases", ["numpy"]),
    ("Apache Spark", "Data & Databases", ["spark", "pyspark"]),
    ("Hadoop", "Data & Databases", []),
    ("ETL", "Data & Databases", ["extract transform load"]),

    # Machine Learning / AI
    ("Machine Learning", "ML & AI", ["ml"]),
    ("Deep Learning", "ML & AI", ["dl"]),
    ("Natural Language Processing", "ML & AI", ["nlp", "natural language processing"]),
    ("Computer Vision", "ML & AI", ["cv", "image recognition"]),
    ("scikit-learn", "ML & AI", ["sklearn", "scikit learn"]),
    ("TensorFlow", "ML & AI", ["tensorflow"]),
    ("PyTorch", "ML & AI", ["pytorch"]),
    ("Keras", "ML & AI", []),
    ("Hugging Face", "ML & AI", ["huggingface", "transformers"]),
    ("XGBoost", "ML & AI", ["xgboost"]),
    ("LightGBM", "ML & AI", []),
    ("OpenCV", "ML & AI", ["opencv"]),
    ("Data Analysis", "ML & AI", ["data analytics", "analytics"]),
    ("Data Visualization", "ML & AI", ["visualization", "data viz"]),
    ("Tableau", "ML & AI", []),
    ("Power BI", "ML & AI", ["powerbi"]),

    # DevOps & Tools
    ("Git", "DevOps & Tools", ["version control", "source control"]),
    ("GitHub", "DevOps & Tools", ["github.com"]),
    ("GitLab", "DevOps & Tools", []),
    ("Docker", "DevOps & Tools", ["containers", "containerization"]),
    ("Kubernetes", "DevOps & Tools", ["k8s"]),
    ("Jenkins", "DevOps & Tools", ["ci/cd", "continuous integration"]),
    ("GitHub Actions", "DevOps & Tools", ["github actions"]),
    ("Terraform", "DevOps & Tools", []),
    ("Ansible", "DevOps & Tools", []),
    ("Linux", "DevOps & Tools", ["unix", "ubuntu", "debian", "centos"]),
    ("Nginx", "DevOps & Tools", []),
    ("Apache", "DevOps & Tools", ["apache httpd"]),
    ("CI/CD", "DevOps & Tools", ["continuous delivery", "continuous deployment"]),

    # Cloud
    ("AWS", "Cloud", ["amazon web services", "amazon aws"]),
    ("Azure", "Cloud", ["microsoft azure"]),
    ("Google Cloud", "Cloud", ["gcp", "google cloud platform"]),
    ("Firebase", "Cloud", []),
    ("Heroku", "Cloud", []),
    ("Cloudflare", "Cloud", []),

    # Testing
    ("Unit Testing", "Testing", ["unit tests"]),
    ("pytest", "Testing", []),
    ("Jest", "Testing", []),
    ("Selenium", "Testing", []),
    ("TDD", "Testing", ["test driven development"]),

    # Soft / Professional
    ("Agile", "Professional Skills", ["scrum", "agile methodology"]),
    ("Jira", "Professional Skills", []),
    ("Confluence", "Professional Skills", []),
    ("Communication", "Professional Skills", []),
    ("Team Leadership", "Professional Skills", ["team lead", "leadership"]),
    ("Project Management", "Professional Skills", []),
]


@dataclass
class _SkillPattern:
    canonical: str
    category: str
    pattern: re.Pattern


def _build_pattern(canonical: str, aliases: list[str]) -> re.Pattern:
    """Build a word-boundary regex for the canonical name and all aliases."""
    terms = [canonical] + aliases
    # For very short tokens like "C", "R", "Go" use strict word boundaries.
    escaped = [re.escape(t) for t in terms]
    combined = "|".join(escaped)
    return re.compile(rf"(?<!\w)({combined})(?!\w)", re.IGNORECASE)


# Build the compiled taxonomy once at import time
_TAXONOMY: list[_SkillPattern] = [
    _SkillPattern(canonical=name, category=cat, pattern=_build_pattern(name, aliases))
    for name, cat, aliases in _RAW_TAXONOMY
]

# Build a quick lookup set for dedup
_CANONICAL_LOWER: dict[str, str] = {s.canonical.lower(): s.canonical for s in _TAXONOMY}


def extract_skills(text: str) -> list[str]:
    """Return a deduplicated list of canonical skill names found in *text*."""
    found: dict[str, str] = {}   # canonical_lower → canonical
    for skill in _TAXONOMY:
        if skill.pattern.search(text):
            key = skill.canonical.lower()
            if key not in found:
                found[key] = skill.canonical
    return list(found.values())


def group_skills_by_category(skills: list[str]) -> dict[str, list[str]]:
    """Group a list of canonical skill names by their taxonomy category."""
    cat_map: dict[str, str] = {s.canonical: s.category for s in _TAXONOMY}
    result: dict[str, list[str]] = {}
    for skill in skills:
        cat = cat_map.get(skill, "Other")
        result.setdefault(cat, []).append(skill)
    return result


def normalize_skill(raw: str) -> str | None:
    """
    Given a free-text skill string (e.g. from user input), return the
    canonical taxonomy name if it matches, else return the stripped input.
    """
    raw = raw.strip()
    for skill in _TAXONOMY:
        if skill.pattern.fullmatch(raw):
            return skill.canonical
    # Case-insensitive exact lookup
    return _CANONICAL_LOWER.get(raw.lower(), raw) if raw else None


def get_all_skill_names() -> list[str]:
    return [s.canonical for s in _TAXONOMY]


def get_categories() -> list[str]:
    seen: list[str] = []
    for _, cat, _ in _RAW_TAXONOMY:
        if cat not in seen:
            seen.append(cat)
    return seen
