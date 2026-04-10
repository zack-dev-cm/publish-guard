#!/usr/bin/env python3
"""Inspect public files for audience-fit and packaging problems."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import subprocess


INTERNAL_DOC_PATTERNS = (
    "social-posts.md",
    "launch-plan.md",
    "publish-checklist.md",
    "github-star-audit.md",
    "reference-patterns.md",
    "demo-script.md",
)
INTERNAL_TERMS = re.compile(
    r"\b(oauth|subagent|main thread|benchmark contract|workflow contract|agent threads|paid api key|control plane)\b",
    re.IGNORECASE,
)


def count_section_bullets(lines: list[str], heading: str) -> int:
    in_section = False
    count = 0
    for line in lines:
        if line.startswith("#"):
            in_section = line.strip().lower() == heading.lower()
            continue
        if in_section and line.lstrip().startswith(("-", "*")):
            count += 1
    return count


def add_finding(findings: list[dict[str, object]], *, code: str, severity: str, file: str, detail: str) -> None:
    findings.append({"code": code, "severity": severity, "file": file, "detail": detail})


def tracked_relative_paths(root: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Repo root to inspect.")
    parser.add_argument("--out", required=True, help="Output JSON file.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings: list[dict[str, object]] = []
    tracked = tracked_relative_paths(root)
    tracked_lookup = {path.as_posix() for path in tracked} if tracked is not None else None

    readme = root / "README.md"
    if readme.exists():
        lines = readme.read_text(encoding="utf-8").splitlines()
        if len(lines) > 220:
            add_finding(findings, code="readme-too-long", severity="warning", file="README.md", detail="README exceeds 220 lines.")
        quick_start_line = next((idx for idx, line in enumerate(lines, start=1) if "quick start" in line.lower()), None)
        if quick_start_line is None or quick_start_line > 80:
            add_finding(findings, code="quick-start-buried", severity="warning", file="README.md", detail="Quick Start heading is missing or too far from the top.")
        first_fence = next((idx for idx, line in enumerate(lines, start=1) if line.strip().startswith("```")), None)
        if first_fence is None or first_fence > 100:
            add_finding(findings, code="no-early-command-example", severity="warning", file="README.md", detail="No early runnable code example near the top of the README.")
        top_text = "\n".join(lines[:60])
        internal_hits = len(INTERNAL_TERMS.findall(top_text))
        if internal_hits >= 4:
            add_finding(findings, code="internal-language-near-top", severity="warning", file="README.md", detail="README intro uses too much internal or operator-facing language.")
        if count_section_bullets(lines, "## what is included") > 20:
            add_finding(findings, code="giant-file-inventory", severity="warning", file="README.md", detail="Large file inventory section is likely low-value for public readers.")

    for doc_name in INTERNAL_DOC_PATTERNS:
        if tracked_lookup is not None:
            matches = sorted(root / rel for rel in tracked if rel.name == doc_name)
        else:
            matches = sorted(root.rglob(doc_name))
        for match in matches:
            add_finding(
                findings,
                code="internal-launch-doc-tracked",
                severity="warning",
                file=str(match.relative_to(root)),
                detail="Internal launch or marketing doc is tracked in the public repo.",
            )

    if tracked_lookup is not None:
        skill_paths = sorted(root / rel for rel in tracked if rel.name == "SKILL.md")
    else:
        skill_paths = sorted(root.rglob("SKILL.md"))
    for skill_path in skill_paths:
        rel_path = str(skill_path.relative_to(root))
        lines = skill_path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 260:
            add_finding(findings, code="skill-too-long", severity="warning", file=rel_path, detail="Public SKILL.md is longer than 260 lines.")
        top_text = "\n".join(lines[:120])
        if len(INTERNAL_TERMS.findall(top_text)) >= 5:
            add_finding(findings, code="skill-too-internal", severity="warning", file=rel_path, detail="Top of SKILL.md reads like internal control text instead of user-facing guidance.")

    if tracked_lookup is not None:
        yaml_paths = sorted(root / rel for rel in tracked if rel.name == "openai.yaml")
    else:
        yaml_paths = sorted(root.rglob("openai.yaml"))
    for yaml_path in yaml_paths:
        rel_path = str(yaml_path.relative_to(root))
        text = yaml_path.read_text(encoding="utf-8")
        default_prompt_line = next((line.strip() for line in text.splitlines() if "default_prompt:" in line), "")
        if default_prompt_line and len(INTERNAL_TERMS.findall(default_prompt_line)) >= 2:
            add_finding(findings, code="public-prompt-too-internal", severity="warning", file=rel_path, detail="Public default prompt exposes too much internal workflow language.")

    payload = {
        "root": str(root),
        "finding_count": len(findings),
        "error_count": sum(1 for item in findings if item["severity"] == "error"),
        "warning_count": sum(1 for item in findings if item["severity"] == "warning"),
        "findings": findings,
    }
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
