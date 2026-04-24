# Security Policy

Publish Guard is a heuristics-based pre-release audit skill. It can help catch obvious public-release problems, but it does not guarantee that a repository is secret-free or safe to publish.

## Supported Versions

Until versioned releases exist, security fixes are handled on the latest state of the default branch.

## Reporting a Vulnerability

- Do not open a public issue for active credential exposure, unpublished launch material, or other sensitive leaks.
- Prefer a GitHub Security Advisory or another non-public maintainer contact path.
- Include the affected commit or files, reproduction steps, impact, and any immediate containment advice.
- If the report involves a live secret, rotate or revoke it first when possible.

## Scope Notes

- Findings about false security claims or misleading public docs are in scope because they can create unsafe release decisions.
- Requests for guaranteed scanning accuracy are out of scope; this project is intentionally heuristic.
