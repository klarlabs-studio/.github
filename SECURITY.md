# Security Policy

This policy applies to every public repository in the
[klarlabs-studio](https://github.com/klarlabs-studio) organization unless a
repository provides its own `SECURITY.md`.

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Report privately through GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
— open the affected repository, go to the **Security** tab, and click
**Report a vulnerability**. If that is unavailable, email **security@klarlabs.de**.

Please include:

- the affected repository and version (tag, commit, or release),
- a description of the issue and its impact,
- reproduction steps or a proof of concept,
- any suggested remediation.

## What to expect

- **Acknowledgement** within 3 business days.
- **Triage and severity assessment** within 7 business days.
- A coordinated fix and disclosure timeline shared with you; we aim to ship a
  patch within 90 days and will keep you updated on progress.
- Credit in the advisory once a fix ships, unless you prefer to remain anonymous.

## Supported versions

Unless a repository states otherwise, security fixes target the **latest
released minor version**. Pre-1.0 libraries are supported on a best-effort basis
at `HEAD`.

## Scope

In scope: source code, build and release pipelines, and published artifacts of
this organization's repositories. Out of scope: vulnerabilities in third-party
dependencies (report those upstream) and findings that require privileged local
access or social engineering.
