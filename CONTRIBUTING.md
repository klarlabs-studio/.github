# Contributing

Thanks for your interest in contributing to a
[klarlabs-studio](https://github.com/klarlabs-studio) project. This guide is the
organization default; a repository may add its own `CONTRIBUTING.md` with
project-specific detail, which takes precedence.

## Before you start

- For anything beyond a trivial fix, **open an issue first** to align on the
  approach before investing in a pull request.
- For security problems, follow the [Security Policy](./SECURITY.md) instead of
  filing a public issue.

## Workflow

1. Fork (external) or branch (internal) from `main`.
2. Make your change with tests.
3. Open a pull request against `main`. Keep it focused — one logical change per PR.
4. CI must pass and the PR must be up to date with `main` before merge.

## Commit and PR conventions

- **[Conventional Commits](https://www.conventionalcommits.org/)** for every
  commit (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`…). Releases
  and changelogs are derived from commit history.
- **Atomic commits** — each commit is a complete, self-contained change.
- Reference the issue the PR closes (`Closes #123`).

## Quality bar

Every change is expected to clear the same gate CI enforces. For Go projects
that means:

- **`gofmt` / formatting** — no unformatted code.
- **Linting** — `golangci-lint` clean.
- **`gocritic`** — no new findings.
- **Tests with the race detector** — `go test -race ./...`, written first (TDD)
  where practical.
- **Coverage** — `coverctl` gate must pass; new code carries tests.
- **Security** — `nox` scan clean.

TypeScript and Python wrappers run the language-equivalent gates (ESLint /
Prettier / `tsc`; `ruff` / formatter / type-check) plus their own tests and the
coverage gate. Run the repo's `make`/task targets locally before pushing.

## Licensing

Unless a repository states otherwise, contributions are accepted under that
repository's license (MIT for most). By submitting a PR you agree your
contribution is licensed under those terms.

## Conduct

All participation is governed by our [Code of Conduct](./CODE_OF_CONDUCT.md).
