cask "pwrsnap" do
  version "1.1.8"
  sha256 "905044acedde410a5ee339fa5fd0142e9dba1743f839927902fdcc10c5ab7c4c"

  # No `verified:` — Homebrew deprecated the parameter (it is now an explicit
  # no-op in `Cask::DSL#url`, and `audit_unnecessary_verified` fails the audit
  # on it). Re-adding it breaks `brew audit --cask`, which is what silently
  # pinned this cask to 1.0.3 through four releases.
  url "https://github.com/pwrdrvr/PwrSnap/releases/download/v#{version}/PwrSnap-#{version}-universal.dmg"
  name "PwrSnap"
  desc "Screen capture, annotation, and recording with optional AI assist"
  homepage "https://pwrsnap.com/"

  # Tracks the Stable train only: /releases/latest never points at a
  # -alpha / -beta / -prerelease tag (CI publishes those as GitHub
  # Pre-releases). Beta testers use the in-app channel switch instead.
  livecheck do
    url :url
    strategy :github_latest
  end

  # PwrSnap updates itself through its GitHub release feed (Settings →
  # General → Check for Updates). `brew upgrade` still works, but Homebrew
  # won't nag about a version the app already moved past.
  auto_updates true
  depends_on macos: :sonoma

  app "PwrSnap.app"

  # Deliberately NOT zapped: ~/Documents/PwrSnap — that folder holds the
  # user's captures (.pwrsnap bundles). Uninstalling the app must never
  # delete screenshots.
  zap trash: [
    "~/Library/Application Support/PwrSnap",
    "~/Library/Caches/com.pwrdrvr.pwrsnap",
    "~/Library/Caches/com.pwrdrvr.pwrsnap.ShipIt",
    "~/Library/Caches/pwrsnap-updater",
    "~/Library/HTTPStorages/com.pwrdrvr.pwrsnap",
    "~/Library/Logs/PwrSnap",
    "~/Library/Preferences/com.pwrdrvr.pwrsnap.plist",
    "~/Library/Saved Application State/com.pwrdrvr.pwrsnap.savedState",
  ]
end
