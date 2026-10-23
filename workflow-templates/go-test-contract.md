# Opt-in test container and verified reuse

`go-ci.yml` keeps its existing host tests unless `test-container-contract` is
supplied. This interface supports a root-module Linux amd64 test job only;
`cross-platform` must be false, `working-directory` must be `.`, and `coverage`
must be true. Lint, build and security jobs always run as before.

Supply a reviewed JSON object from protected caller configuration:

```json
{
  "image": "ghcr.io/OWNER/IMAGE@sha256:REVIEWED_MANIFEST_DIGEST",
  "config_id": "sha256:REVIEWED_DOCKER_CONFIG_DIGEST",
  "platform": "linux/amd64",
  "command": "/usr/local/bin/test-contract",
  "signing_identity": "https://github.com/OWNER/REPO/.github/workflows/image.yml@refs/heads/main"
}
```

Use real immutable digests. The executable must perform the entire test and
coverage gate, exit nonzero when either fails, and write `coverage.out` in
`/workspace`. It executes without arguments or a shell wrapper. The image must
support arbitrary non-root UIDs. The workflow verifies its exact keyless
publisher identity, pulls the digest and compares Docker's config identity and
platform before running as UID/GID 10001, HOME=/tmp, with no network access.
Coverage thresholds remain the caller's reviewed policy. Existing host-only
checks and the container command must be reviewed for equivalence before opting
in. Dependency changes require a newly prepared image if modules are uncached.

The container checks out the pull request head, because local evidence binds
that commit. It does not validate GitHub's synthetic merge commit. Callers that
require merge-result testing must keep a separate merge-result gate. Default
host tests retain their existing checkout behavior.

`test-reuse-sha` defaults to empty, so the container command runs. A caller may
supply the exact candidate SHA only after a protected verifier has checked the
trusted signature, commit binding and the complete execution contract, including
command, effective configuration, inputs, comparison base, branch context,
platform, image identity and network policy. On PRs the candidate is
`github.event.pull_request.head.sha`; otherwise it is `github.sha`.

This workflow does not authenticate a caller's reuse claim. That is the caller's
responsibility. Never pass a candidate-controlled boolean, note field, artifact,
policy or unverified SHA directly. The caller must execute reviewed verifier
code, obtain expectations independently of the note and fall back to an empty
SHA on errors or missing evidence. Distinct image identity kinds and platforms
remain distinct contracts; an Apple arm64 pass does not replace this Docker
amd64 job.

An exact reuse SHA retains the `Test` check and records that it accepted the
caller's verifier decision; it executes no remote tests, checkout or tool setup.
An incorrect or malformed SHA runs the container contract instead. A reuse claim
without an explicit valid contract fails. Malformed contracts and unsupported
scope fail the job. Other required CI jobs cannot be skipped through this input.

Do not feed the reused result back as fresh execution evidence. It is a consumer
of the original signed local observation. Measurement should distinguish actual
remote execution from accepted reuse.

Run the interface regression tests with:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

They need Bash, jq, Python 3 and Ruby's standard YAML/JSON libraries. The tests
execute the actual selector embedded in the workflow; no registry access is
needed. Image equivalence and successful offline execution still need live
validation by each adopting caller.
