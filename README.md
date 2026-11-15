[![nox security grade](.github/nox-badge.svg)](.github/workflows/nox.yml)

# klarlabs-studio/.github

Organization-wide defaults and shared CI for the
[klarlabs-studio](https://github.com/klarlabs-studio) repositories.

## Contents

| Path | Purpose |
| :-- | :-- |
| `profile/` | The organization profile page (`profile/README.md`) and its logo assets. |
| `SECURITY.md`, `CONTRIBUTING.md` | Default security policy and contribution guide for repositories that do not ship their own. |
| `.github/workflows/go-ci.yml`, `js-ci.yml` | Reusable (`workflow_call`) CI for Go and JavaScript repositories, including the nox scan and gate. |
| `.github/workflows/nox.yml` | Reusable nox scan and gate for repositories without go-ci or js-ci. The nox version is pinned here. |
| `.github/workflows/nox-remediate.yml` | Reusable weekly remediation of vulnerable dependencies and stale action pins. |
| `.github/workflows/nox-pin-check.yml` | Weekly job that opens a PR when a newer nox release is available (`scripts/nox-pin.sh`). |
| `.github/workflows/test-go-contract.yml` | Tests the go-ci contract interface (`scripts/test_go_ci_contract.py`). |
| `workflow-templates/` | Starter workflows offered in the organization's Actions tab, with `*.properties.json` metadata. |
| `nox.reference.yaml`, `golangci.reference.yml` | Reference configurations for nox and golangci-lint. |

## Notes for changes

- The reusable workflows are consumed by other repositories through
  `klarlabs-studio/.github/.github/workflows/<name>.yml@main`. Changing a
  workflow input name or default affects every caller.
- The nox version is pinned in one place per workflow and kept in step by
  `scripts/nox-pin.sh`.
- The grade badge (`.github/nox-badge.svg`) is a snapshot. Regenerate it with
  `nox badge -output .github/nox-badge.svg` after any change that alters scan
  results.
