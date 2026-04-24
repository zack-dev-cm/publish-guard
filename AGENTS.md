# AGENTS.md

This repository ships one public skill, `publish-guard`. Use this file as the index, not as the full manual.

## Operating rules

- Restate the user goal and name the verification step before editing files.
- Keep diffs surgical. Do not broaden beyond the requested release-surface work.
- Preserve the split between top-level repo scaffolding and `skill/publish-guard/` implementation details.
- Keep repo positioning honest: this is a heuristics-based pre-release audit skill, not a perfect scanner.
- Put durable knowledge in `docs/codex/`. Keep this file short.

## Repo map

- [Overview](docs/codex/overview.md)
- [Architecture](docs/codex/architecture.md)
- [Workflow](docs/codex/workflow.md)
- [Evals](docs/codex/evals.md)
- [Cleanup](docs/codex/cleanup.md)

## Main code paths

- `skill/publish-guard/`: public skill manifest, agent metadata, and audit scripts.
- `docs/`: user-facing docs and release guidance.
- `.github/`: CI and pull request template.

## Default verification

1. Run `python3 -m py_compile skill/publish-guard/scripts/*.py tests/*.py`.
2. Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`.
3. Run the smallest relevant smoke path for the touched script or metadata surface.
4. Optional portfolio-level gate: if you are working from the external control workspace that already provides `codex_harness`, run `PYTHONPATH=/path/to/github_stars_optimizer python3 -m codex_harness audit . --strict --min-score 90`.
5. If public copy changed, review `README.md`, `SKILL.md`, and docs for overclaims, leaks, and broken commands.

## Project-scoped custom agents

- `.codex/agents/architect.toml`
- `.codex/agents/implementer.toml`
- `.codex/agents/reviewer.toml`
- `.codex/agents/evolver.toml`
- `.codex/agents/cleanup.toml`
