# Contributing

Thanks for contributing to Publish Guard.

## Ground rules

- Keep diffs small and directly tied to the issue being solved.
- Keep public docs aligned with the actual scripts and current CI.
- Do not add claims of perfect scanning or exhaustive security coverage.
- Avoid committing generated artifacts such as `__pycache__/`.

## Development checklist

1. Read the smallest relevant script or doc before editing.
2. Make the minimal durable change.
3. Run `python3 -m py_compile skill/publish-guard/scripts/*.py tests/*.py`.
4. Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`.
5. Run the smallest relevant smoke path for the changed script or metadata surface.
6. Optional portfolio-level gate: if you are working from the external control workspace that already provides `codex_harness`, run `PYTHONPATH=/path/to/github_stars_optimizer python3 -m codex_harness audit . --strict --min-score 90`.
7. Review public-facing files for leaks, overclaims, and broken commands.

## Pull requests

- Explain what changed and why.
- List the verification you ran.
- Note any assumptions, follow-up work, or intentionally deferred gaps.

Large changes should start with an issue or a short design note so scope stays clear.
