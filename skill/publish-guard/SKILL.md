---
name: publish-guard
description: Review a repo, README, SKILL.md, release notes, and social copy before publishing. Catch leak risks, weak public-facing copy, broken first-run paths, and internal operator language before GitHub or ClawHub release.
homepage: https://zack-dev-cm.github.io/
license: MIT-0
user-invocable: true
metadata: {"openclaw":{"homepage":"https://zack-dev-cm.github.io/","skillKey":"publish-guard","requires":{"anyBins":["python3","python"]}}}
---

# Publish Guard

## Goal

Audit the public surface before release:

- README
- `SKILL.md`
- agent metadata
- release notes
- social copy
- obvious leak patterns

The output should answer one question clearly: publish now, or fix specific items first.

## Use This Skill When

- the user wants to publish a GitHub repo or ClawHub skill
- the user wants a public-surface audit before a launch
- the repo may contain internal launch docs, secret-shaped strings, or operator-only wording
- the README or `SKILL.md` feels too insider-heavy or too long
- the first-run path may be broken, vague, or buried

## Quick Start

1. Scan for obvious leak patterns.
   - `python3 {baseDir}/scripts/scan_leaks.py --root <repo> --out <json>`
2. Scan the public surface for audience-fit problems.
   - `python3 {baseDir}/scripts/scan_public_surface.py --root <repo> --out <json>`
3. Score the README or primary landing page.
   - `python3 {baseDir}/scripts/score_launch_copy.py --readme <repo>/README.md --out <json>`
4. Render one decision-ready audit.
   - `python3 {baseDir}/scripts/render_public_audit.py --repo <repo> --leaks <json> --surface <json> --copy <json> --out <md>`

## Operating Rules

- Treat `README.md`, `SKILL.md`, `agents/openai.yaml`, release notes, and social-post files as public.
- Public copy should describe the user job before it explains the internal theory.
- A public quick start should appear near the top and should be runnable without hidden context.
- Keep public default prompts short. Move deeper operating rules into the skill body or scripts.
- Flag internal launch docs in the repo unless they are intentionally private and excluded from the public package.
- Prefer a small set of concrete findings over a broad essay.

## What To Flag

- absolute filesystem paths
- localhost URLs and websocket endpoints
- token-shaped strings and credential-like URLs
- missing or buried quick starts
- giant inventory sections or excessively long `SKILL.md` files
- public prompts that read like internal control instructions
- README intros that compare the repo to five other projects before explaining what it does

## Bundled Scripts

- `scripts/scan_leaks.py`
  - Search the repo for obvious leak patterns and secret-shaped strings.
- `scripts/scan_public_surface.py`
  - Inspect README, `SKILL.md`, release notes, and public metadata for audience-fit issues.
- `scripts/score_launch_copy.py`
  - Produce a simple launch-copy score for the primary README.
- `scripts/render_public_audit.py`
  - Merge the JSON outputs into one concise markdown audit.
