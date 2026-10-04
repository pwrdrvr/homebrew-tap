#!/usr/bin/env bash
set -euo pipefail
candidate=${1:?candidate cask path required}
previous=${2:-}
token=pwrdrvr/tap/pwrgit
mkdir -p "$(brew --repository)/Library/Taps/pwrdrvr"
if [ ! -L "$(brew --repository)/Library/Taps/pwrdrvr/homebrew-tap" ]; then
  ln -s "$PWD" "$(brew --repository)/Library/Taps/pwrdrvr/homebrew-tap"
fi
if brew trust --help >/dev/null 2>&1; then brew trust --cask "$token"; fi

# On updates, exercise replacement from the currently published version.
current=$(sed -nE 's/^  version "([0-9]+\.[0-9]+\.[0-9]+)"/\1/p' Casks/pwrgit.rb)
target=$(sed -nE 's/^  version "([0-9]+\.[0-9]+\.[0-9]+)"/\1/p' "$candidate")
test -n "$target"
if [ "$current" != "$target" ] && [ "$previous" = "$current" ]; then
  brew install --cask "$token"
fi
cp "$candidate" Casks/pwrgit.rb
brew style --cask "$token"
brew audit --cask --online "$token"
if [ "$current" != "$target" ] && [ "$previous" = "$current" ]; then
  brew upgrade --cask --greedy "$token"
else
  brew install --cask "$token"
fi
app=/Applications/PwrGit.app
test -d "$app"
test ! -L "$app"
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' "$app/Contents/Info.plist")" = com.pwrdrvr.pwrgit
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$app/Contents/Info.plist")" = "$target"
codesign --verify --deep --strict "$app"
codesign -dv --verbose=2 "$app" 2>&1 | grep -q 'Authority=Developer ID Application: PwrDrvr LLC'
spctl --assess --type execute --verbose=2 "$app"
slices=$(lipo -archs "$app/Contents/MacOS/PwrGit")
if [ "$(uname -m)" = arm64 ]; then
  test "$slices" = arm64
else
  echo "$slices" | grep -qw x86_64
  echo "$slices" | grep -qw arm64
fi
brew uninstall --cask "$token"
test ! -e "$app"
echo "Verified PwrGit $target: cask audit, install/upgrade, architecture, signatures and uninstall."
