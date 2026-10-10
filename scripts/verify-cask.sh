#!/usr/bin/env bash
set -euo pipefail
cask=${1:?cask token required}
candidate=${2:?candidate path required}
previous=${3:?previous version required}
token="pwrdrvr/tap/$cask"
test "$(sed -nE 's/^  version "([0-9]+\.[0-9]+\.[0-9]+)"/\1/p' "Casks/$cask.rb")" = "$previous"
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
export HOMEBREW_CURL_PATH="$PWD/scripts/ci-curl.py"
if brew trust --help >/dev/null 2>&1; then brew trust --cask "$token"; fi
installed=false
cleanup() {
  if $installed; then brew uninstall --cask "$token"; fi
}
trap cleanup EXIT
brew install --cask "$token"
installed=true
appname=$(brew info --json=v2 --cask "$token" | python3 -c 'import json,sys; c=json.load(sys.stdin)["casks"][0]; print(next(a["app"][0] for a in c["artifacts"] if "app" in a))')
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "/Applications/$appname/Contents/Info.plist")" = "$previous"
cp "$candidate" "Casks/$cask.rb"
brew style "Casks/$cask.rb"
# Release metadata verifies the URL; probing it would bypass artifact-only CI.
brew audit --cask --online --except=url_https_availability "$token"
brew upgrade --cask --greedy "$token"
target=$(sed -nE 's/^  version "([0-9]+\.[0-9]+\.[0-9]+)"/\1/p' "$candidate")
case "$cask" in
  pwrgit) appname=PwrGit; bundle=com.pwrdrvr.pwrgit ;;
  pwrsnap) appname=PwrSnap; bundle=com.pwrdrvr.pwrsnap ;;
  pwragent) appname=PwrAgent; bundle=com.pwrdrvr.pwragent ;;
  *) exit 1 ;;
esac
app="/Applications/$appname.app"
test -d "$app"
test ! -L "$app"
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' "$app/Contents/Info.plist")" = "$bundle"
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$app/Contents/Info.plist")" = "$target"
test "$(/usr/libexec/PlistBuddy -c 'Print LSMinimumSystemVersion' "$app/Contents/Info.plist")" = "${MINIMUM_OS:?release minimum OS required}"
codesign --verify --deep --strict "$app"
codesign -dv --verbose=2 "$app" 2>&1 | grep -q 'TeamIdentifier=T44CNHC4UH'
spctl --assess --type execute --verbose=2 "$app"
xcrun stapler validate "$app"
slices=$(lipo -archs "$app/Contents/MacOS/$appname")
echo "$slices" | grep -qw "$(uname -m)"
if [[ "$cask" == pwrsnap || "$(uname -m)" == x86_64 ]]; then
  echo "$slices" | grep -qw arm64
  echo "$slices" | grep -qw x86_64
else
  test "$slices" = arm64
fi
brew uninstall --cask "$token"
installed=false
test ! -e "$app"
# Fresh candidate installation reuses the same verified artifact cache.
brew install --cask "$token"
installed=true
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$app/Contents/Info.plist")" = "$target"
brew uninstall --cask "$token"
installed=false
test ! -e "$app"
echo "Verified $appname $previous -> $target: artifact-backed install/upgrade, signature, notarization, architecture and uninstall"
