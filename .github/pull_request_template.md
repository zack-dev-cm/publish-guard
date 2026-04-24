## Summary

- Describe the change.
- Describe why it is needed.

## Verification

- [ ] `python3 -m py_compile skill/publish-guard/scripts/*.py tests/*.py`
- [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`
- [ ] If using the external control workspace: `PYTHONPATH=/path/to/github_stars_optimizer python3 -m codex_harness audit . --strict --min-score 90`

## Public Surface Review

- [ ] Security, leak, and public-surface review is complete
- [ ] No new secrets, private paths, localhost URLs, or internal-only language
- [ ] No new claims of perfect or exhaustive scanning
- [ ] README, skill docs, and repo docs stay aligned with actual behavior

## Assumptions And Follow-ups

- List assumptions, deferred work, or known limitations.
