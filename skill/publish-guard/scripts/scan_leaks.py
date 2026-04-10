#!/usr/bin/env python3
"""Scan a repo for common public-release leak patterns."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import subprocess


TEXT_EXTENSIONS = {
    ".env",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORE_DIRS = {".git", "__pycache__", "dist", "build", "node_modules", ".venv", "venv"}
MAX_BYTES = 512_000
PATTERNS = [
    ("absolute-path", "error", re.compile(r"(/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\\\Users\\\\[^\\\s]+\\\\)")),
    ("websocket-endpoint", "error", re.compile(r"\bws://|\bwss://")),
    ("localhost-url", "warning", re.compile(r"(https?://(?:localhost|127\.0\.0\.1)\b|\b(?:localhost|127\.0\.0\.1):\d+)")),
    ("github-token", "error", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]+\b|\bgithub_pat_[A-Za-z0-9_]+\b")),
    ("openai-key", "error", re.compile(r"\bsk-[A-Za-z0-9]{12,}\b")),
    ("slack-token", "error", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b")),
    (
        "secret-env-var",
        "warning",
        re.compile(
            r"(?:(?:export\s+)?(OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY|GOOGLE_API_KEY|CEREBRAS_API_KEY)\s*[:=]\s*[\"']?[A-Za-z0-9._-]{6,})"
        ),
    ),
    ("credential-url", "error", re.compile(r"https?://[^/\s:@]+:[^/\s:@]+@")),
]


def tracked_files(root: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = root / line.strip()
        if path.is_file():
            paths.append(path)
    return sorted(paths)


def iter_files(root: Path) -> list[Path]:
    tracked = tracked_files(root)
    if tracked is not None:
        return [
            path
            for path in tracked
            if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"README", "LICENSE", "SKILL.md"}
        ]

    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS or part.startswith(".venv") for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in {"README", "LICENSE", "SKILL.md"}:
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
        except OSError:
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Repo root to scan.")
    parser.add_argument("--out", required=True, help="Output JSON file.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings: list[dict[str, object]] = []

    for path in iter_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if "re.compile(" in line:
                continue
            for code, severity, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "code": code,
                            "severity": severity,
                            "file": str(path.relative_to(root)),
                            "line": line_number,
                            "snippet": line.strip()[:220],
                        }
                    )

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
