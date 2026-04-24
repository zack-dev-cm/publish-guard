# Architecture

## Boundaries

- `skill/publish-guard/SKILL.md`: user-facing skill contract and operating guidance.
- `skill/publish-guard/agents/openai.yaml`: runtime-facing agent metadata for the skill.
- `skill/publish-guard/scripts/*.py`: heuristic scanners and report renderer.
- Top-level docs: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `docs/codex/` keep the public repo surface honest.

## Shared design rules

- Keep heuristic logic explicit in scripts and mirrored honestly in docs.
- Prefer concise, decision-ready findings over broad essays.
- Treat examples, templates, and release docs as part of the product surface.
- Keep local-first usage viable without hidden services or private infrastructure.

## Do-not-break list

- Public skill identity: `publish-guard`
- Script entrypoints: `scan_leaks.py`, `scan_public_surface.py`, `score_launch_copy.py`, `render_public_audit.py`
- Release-facing docs in `README.md`, `docs/`, `SECURITY.md`, and `CONTRIBUTING.md`
- Honest positioning: useful heuristic pre-release audit, not guaranteed leak detection
