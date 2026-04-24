# Evals

## Rules

- Every task should name the primary check before editing.
- Public-surface changes need leak and overclaim review, not just a passing syntax check.
- Prefer deterministic local checks before broad manual inspection.
- Until dedicated tests exist, syntax plus a representative smoke path are the minimum bar.

## Required checks

- Syntax: `python3 -m py_compile skill/publish-guard/scripts/*.py`
- Relevant smoke: run the smallest affected script with `--help` or a representative invocation
- Public docs review: verify `README.md`, `SKILL.md`, `SECURITY.md`, `CONTRIBUTING.md`, and the PR template do not promise coverage the scripts do not provide

## Quality bar

- Claims of perfect detection, exhaustive scanning, or guaranteed safety are failures.
- Secret-shaped strings, private paths, internal URLs, and accidentally tracked generated artifacts are release blockers.
- Drift between scripts and public docs is a product bug, not optional polish.
