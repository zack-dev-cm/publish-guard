# Workflow

## Default loop

1. Clarify the exact release surface being prepared and the primary verification step.
2. Read the smallest relevant script, docs, and metadata files.
3. Implement the smallest durable change.
4. Review for correctness, regressions, leaks, and public-surface overclaims.
5. Run the highest-signal local checks.
6. Update docs or templates when the change introduces a new durable rule.

## Release-audit loop

1. Harden metadata: README, SECURITY, CONTRIBUTING, and PR template.
2. Harden public copy: keep the user job clear and the first-run path near the top.
3. Harden findings: focus on likely leaks, audience mismatch, and broken launch paths.
4. Harden scope: remove false assurance and avoid pretending the heuristics are exhaustive.
5. Re-run the relevant local check before handing off.

## When to use which agent

- `architect`: ambiguous release-surface scope or repo-boundary decisions.
- `implementer`: focused code or docs work.
- `reviewer`: final correctness, leak, and public-surface review.
- `evolver`: measured tuning of heuristics or report wording.
- `cleanup`: post-merge drift control and removal of stale public artifacts.
