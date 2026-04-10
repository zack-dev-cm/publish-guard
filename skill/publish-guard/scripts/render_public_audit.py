#!/usr/bin/env python3
"""Render a concise markdown audit from Publish Guard JSON outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str) -> dict[str, object]:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def top_findings(payload: dict[str, object], limit: int = 5) -> list[dict[str, object]]:
    findings = payload.get("findings") or []
    findings = sorted(
        findings,
        key=lambda item: (0 if item.get("severity") == "error" else 1, str(item.get("file", "")), int(item.get("line", 0) or 0)),
    )
    return findings[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Repo root.")
    parser.add_argument("--leaks", required=True, help="Path to leak-scan JSON.")
    parser.add_argument("--surface", required=True, help="Path to public-surface JSON.")
    parser.add_argument("--copy", required=True, help="Path to launch-copy JSON.")
    parser.add_argument("--out", required=True, help="Output markdown path.")
    args = parser.parse_args()

    leaks = load_json(args.leaks)
    surface = load_json(args.surface)
    copy = load_json(args.copy)

    error_count = int(leaks.get("error_count", 0)) + int(surface.get("error_count", 0))
    warning_count = int(leaks.get("warning_count", 0)) + int(surface.get("warning_count", 0))
    copy_score = int(copy.get("score", 0))

    if error_count == 0 and copy_score >= 80:
        recommendation = "Publish"
    elif error_count == 0 and copy_score >= 60:
        recommendation = "Fix copy first"
    else:
        recommendation = "Do not publish yet"

    lines = [
        "# Publish Guard Audit",
        "",
        f"- Repo: `{Path(args.repo).expanduser().resolve()}`",
        f"- Recommendation: **{recommendation}**",
        f"- Launch copy score: **{copy_score}/100** ({copy.get('verdict', 'unknown')})",
        f"- Leak scan: **{leaks.get('finding_count', 0)}** findings",
        f"- Public surface scan: **{surface.get('finding_count', 0)}** findings",
        f"- Errors: **{error_count}**",
        f"- Warnings: **{warning_count}**",
        "",
    ]

    lines.append("## Top Leak Findings")
    leak_findings = top_findings(leaks)
    if leak_findings:
        for item in leak_findings:
            location = f"{item.get('file')}:{item.get('line')}" if item.get("line") else str(item.get("file"))
            lines.append(f"- `{item.get('severity')}` `{item.get('code')}` {location}: {item.get('snippet', '')}")
    else:
        lines.append("- No obvious leak patterns detected.")
    lines.append("")

    lines.append("## Top Public Surface Findings")
    surface_findings = top_findings(surface)
    if surface_findings:
        for item in surface_findings:
            lines.append(f"- `{item.get('severity')}` `{item.get('code')}` {item.get('file')}: {item.get('detail')}")
    else:
        lines.append("- No major public-surface issues detected.")
    lines.append("")

    lines.append("## Launch Copy Components")
    for item in copy.get("components", []):
        lines.append(f"- `{item.get('delta', 0):+}` {item.get('name')}: {item.get('detail')}")
    lines.append("")

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
