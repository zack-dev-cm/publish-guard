# Publish Guard

**Review a repo, README, `SKILL.md`, and release surface before you publish.**

Publish Guard is a small public OpenClaw skill for pre-release audits. It catches obvious leak risks,
public-audience mismatch, weak first-run copy signals, and launch-surface problems before a GitHub repo or
ClawHub skill goes live.

## Proof

```md
# Publish Guard Audit

- Recommendation: **Publish**
- Launch copy score: **100/100** (publish-ready)
- Leak scan: **0** findings
- Public surface scan: **0** findings
```

## Quick Start

```bash
python3 skill/publish-guard/scripts/scan_leaks.py \
  --root . \
  --out /tmp/publish-guard-leaks.json

python3 skill/publish-guard/scripts/scan_public_surface.py \
  --root . \
  --out /tmp/publish-guard-surface.json

python3 skill/publish-guard/scripts/score_launch_copy.py \
  --readme README.md \
  --out /tmp/publish-guard-copy.json

python3 skill/publish-guard/scripts/render_public_audit.py \
  --repo . \
  --leaks /tmp/publish-guard-leaks.json \
  --surface /tmp/publish-guard-surface.json \
  --copy /tmp/publish-guard-copy.json \
  --out /tmp/publish-guard-audit.md
```

## What It Catches

- absolute paths, localhost URLs, websocket endpoints, and token-shaped strings
- operator-facing or internal language near the top of a public README
- missing or buried quick starts
- oversized public `SKILL.md` files
- internal launch docs accidentally left in a public repo
- public prompts and metadata that read like internal control text instead of a user-facing product

## Included

- `skill/publish-guard/SKILL.md`
- `skill/publish-guard/agents/openai.yaml`
- `skill/publish-guard/scripts/scan_leaks.py`
- `skill/publish-guard/scripts/scan_public_surface.py`
- `skill/publish-guard/scripts/score_launch_copy.py`
- `skill/publish-guard/scripts/render_public_audit.py`

## Use Cases

- review a GitHub repo before making it public
- review a ClawHub skill before publishing or bumping a version
- compare two README directions and choose the cleaner public story
- audit public metadata and launch docs in the working tree for leaks and audience mismatch

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure and scope notes.

## License

MIT No Attribution (MIT-0)
