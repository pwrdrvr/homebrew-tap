#!/usr/bin/env bash
# Bump Casks/pwrsnap.rb to a given PwrSnap version.
#
#   scripts/bump-cask.sh 1.0.4
#
# Verifies (or reuses) the versioned DMG against GitHub's release digest
# and rewrites the cask. The scheduled workflow resolves separately on Linux.
set -euo pipefail

v="${1:?usage: bump-cask.sh <version-without-leading-v>}"
v="${v#v}"
cask="$(cd "$(dirname "${0}")/.." && pwd)/Casks/pwrsnap.rb"
cd "$(dirname "${cask}")/.."
url="https://github.com/pwrdrvr/PwrSnap/releases/download/v${v}/PwrSnap-${v}-universal.dmg"

python3 scripts/installer-cache.py plan --plan .local/pwrsnap-installer.json \
  --url "$url" --version "$v" --architecture universal --from-release
python3 scripts/installer-cache.py ensure --plan .local/pwrsnap-installer.json
sha="$(python3 -c 'import json; print(json.load(open(".local/pwrsnap-installer.json"))["sha256"])')"

# perl -pi is portable across macOS + Linux (sed -i differs).
perl -pi -e "s/^  version \".*\"/  version \"${v}\"/; s/^  sha256 \".*\"/  sha256 \"${sha}\"/" "${cask}"

echo "pwrsnap cask -> ${v} (${sha})"
git -C "$(dirname "${cask}")/.." diff --stat -- Casks/pwrsnap.rb || true
