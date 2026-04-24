# Cleanup

Codex can add drift quickly, even in a small repo. This file defines the cleanup cadence.

## Weekly sweep

- Refresh docs that drifted from the current scripts or CI.
- Remove stale release notes, copied internal language, and generated artifacts.
- Tighten repeated review comments into templates, docs, or script checks.
- Re-run the baseline syntax check after cleanup.

## Promote a rule when

- The same leak or overclaim issue appears more than once.
- Review repeatedly asks for the same public metadata or wording fix.
- A stale example or template creates a false first-run path.

## Do not do

- Large opportunistic rewrites under the label of cleanup.
- Generated-file churn with no user-facing value.
- New abstractions that blur the boundary between repo scaffolding and skill implementation.
