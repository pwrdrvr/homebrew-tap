#!/usr/bin/env bash
# Bump Casks/pwrsnap.rb to a given PwrSnap version.
#
#   scripts/bump-cask.sh 1.0.4
#
# Downloads the universal DMG for that tag from GitHub Releases, computes
# its sha256, and rewrites the `version` / `sha256` stanzas. Commit the
# result (CI does this for you via .github/workflows/bump.yml).
set -euo pipefail

v="${1:?usage: bump-cask.sh <version-without-leading-v>}"
v="${v#v}"
cask="$(cd "$(dirname "${0}")/.." && pwd)/Casks/pwrsnap.rb"
url="https://github.com/pwrdrvr/PwrSnap/releases/download/v${v}/PwrSnap-${v}-universal.dmg"

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

echo "Fetching ${url}"
curl -fsSL --retry 3 -o "${tmp}/PwrSnap.dmg" "${url}"
sha="$(shasum -a 256 "${tmp}/PwrSnap.dmg" | cut -d' ' -f1)"

# perl -pi is portable across macOS + Linux (sed -i differs).
perl -pi -e "s/^  version \".*\"/  version \"${v}\"/; s/^  sha256 \".*\"/  sha256 \"${sha}\"/" "${cask}"

echo "pwrsnap cask -> ${v} (${sha})"
git -C "$(dirname "${cask}")/.." diff --stat -- Casks/pwrsnap.rb || true
