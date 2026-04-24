# Overview

This repository packages Publish Guard, a small public pre-release audit skill for GitHub repos and ClawHub launches.

## Product

- `publish-guard`: reviews public-facing repo assets such as `README.md`, `SKILL.md`, agent metadata, and launch docs in the working tree for likely leaks, audience mismatch, and weak first-run copy signals.

## Repo landmarks

- Skill package: `skill/publish-guard/`
- Public docs: `README.md`, `docs/`, `SECURITY.md`, `CONTRIBUTING.md`
- GitHub automation: `.github/workflows/`, `.github/pull_request_template.md`

## Standard checks

- Syntax: `python3 -m py_compile skill/publish-guard/scripts/*.py tests/*.py`
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`
- Smoke: run the smallest relevant script `--help` path or representative invocation
- Optional external portfolio gate: `PYTHONPATH=/path/to/github_stars_optimizer python3 -m codex_harness audit . --strict --min-score 90` when you are already running from the control workspace that provides `codex_harness`
- Public-surface review: inspect README, skill docs, and templates for leaks and overclaims

## Non-goals

- This repo is not a hosted service.
- It is not a perfect secret scanner or a substitute for full security review.
- It should stay narrow, local-first, and explicit about heuristic behavior.
