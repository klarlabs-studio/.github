#!/usr/bin/env bash
# Resolve the newest nox release, verify its checksums are signed, and rewrite
# the three pins. Prints "up-to-date" and exits 0 when nothing needs doing.
#
# Every failure here is fatal on purpose. A pin checker that shrugs off a failed
# download or an unverifiable signature is worse than no checker: it reports
# success while the fleet quietly stays behind, which is exactly how
# nox-remediate reached 1.19.0 while go-ci was on 1.24.0.
set -euo pipefail

REPO="${NOX_REPO:-Nox-HQ/nox}"
WORKFLOWS=(.github/workflows/go-ci.yml .github/workflows/js-ci.yml .github/workflows/nox-remediate.yml)

# Read EVERY pin, not just the first. Reading one and trusting it is how this
# drifted in the first place: go-ci sat on 1.24.0 while nox-remediate was six
# releases behind on 1.19.0, and any check that sampled go-ci alone would have
# called that fleet up-to-date.
pins=()
for f in "${WORKFLOWS[@]}"; do
  v="$(grep -A3 'nox-version:' "$f" | grep -m1 'default:' | sed 's/.*"\(.*\)".*/\1/')"
  [ -n "$v" ] || { echo "$f: could not read its nox-version pin" >&2; exit 1; }
  echo "current pin: ${v}  (${f##*/})"
  pins+=("$v")
done

tag="$(gh api "repos/${REPO}/releases/latest" --jq .tag_name)"
[ -n "$tag" ] || { echo "could not resolve the latest release tag" >&2; exit 1; }
latest="${tag#v}"
echo "latest:      ${latest}"

behind=0
for v in "${pins[@]}"; do
  [ "$v" = "$latest" ] || behind=$((behind + 1))
done

if [ "$behind" -eq 0 ]; then
  echo "up-to-date"
  exit 0
fi
if [ "$behind" -ne "${#WORKFLOWS[@]}" ]; then
  echo "note: ${behind} of ${#WORKFLOWS[@]} pins are behind — they had drifted apart" >&2
fi
current="${pins[0]}"  # only quoted in the message when all pins agreed

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
gh release download "$tag" --repo "$REPO" --pattern "checksums.txt" --dir "$tmp"
gh release download "$tag" --repo "$REPO" --pattern "checksums.txt.sig.bundle" --dir "$tmp"

# The pin exists so a swapped binary is caught. Taking its value from an
# unverified checksums.txt would hand that guarantee to whoever can rewrite the
# release, so the file must carry a valid keyless signature from this repo's
# own release workflow at this exact tag.
cosign verify-blob "$tmp/checksums.txt" \
  --bundle "$tmp/checksums.txt.sig.bundle" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp "^https://github.com/${REPO}/\.github/workflows/release\.yml@refs/tags/v"

asset="nox_${latest}_linux_amd64.tar.gz"
sha="$(awk -v a="$asset" '$2==a{print $1}' "$tmp/checksums.txt")"
[ -n "$sha" ] || { echo "no checksum for ${asset} in the signed checksums.txt" >&2; exit 1; }
echo "sha256:      ${sha}"

rewritten=0
for f in "${WORKFLOWS[@]}"; do
  v="$(grep -A3 'nox-version:' "$f" | grep -m1 'default:' | sed 's/.*"\(.*\)".*/\1/')"
  s="$(grep -A3 'nox-sha256:' "$f" | grep -m1 'default:' | sed 's/.*"\(.*\)".*/\1/')"
  [ -n "$v" ] && [ -n "$s" ] || { echo "$f: could not read its pin" >&2; exit 1; }

  before="$(cat "$f")"
  perl -0pi -e "s/\Q\"$v\"\E/\"$latest\"/; s/\Q\"$s\"\E/\"$sha\"/" "$f"

  # Compare content, not `git diff`. Whether the file differs from HEAD depends
  # on what HEAD happens to hold; whether the rewrite fired does not.
  if [ "$before" != "$(cat "$f")" ]; then
    rewritten=$((rewritten + 1))
  elif [ "$v" != "$latest" ] || [ "$s" != "$sha" ]; then
    echo "$f: pin is ${v}/${s:0:12} but the rewrite changed nothing" >&2
    exit 1
  fi
done

# Every workflow must now agree, whether it was rewritten or was already there.
for f in "${WORKFLOWS[@]}"; do
  v="$(grep -A3 'nox-version:' "$f" | grep -m1 'default:' | sed 's/.*"\(.*\)".*/\1/')"
  s="$(grep -A3 'nox-sha256:' "$f" | grep -m1 'default:' | sed 's/.*"\(.*\)".*/\1/')"
  [ "$v" = "$latest" ] && [ "$s" = "$sha" ] || {
    echo "$f: still on ${v}/${s:0:12} after the bump — a partial bump is worse than none" >&2
    exit 1
  }
done
echo "rewritten: ${rewritten} of ${#WORKFLOWS[@]}"

if [ "$behind" -eq "${#WORKFLOWS[@]}" ]; then
  echo "bumped ${current} -> ${latest}"
else
  echo "realigned ${behind} drifted pin(s) to ${latest}"
fi
