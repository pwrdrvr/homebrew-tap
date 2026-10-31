cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.49.0"
  sha256 arm:   "736b46a6c258d1441b842d74ecbc2579ec2bf35f2df0bcc7ca57625c7dc982ef",
         intel: "8984b03c28632fb3f24e43add0c6aa77adb6b7a2e12e95b934be63e353127b8f"

  url "https://github.com/pwrdrvr/PwrGit/releases/download/v#{version}/PwrGit-#{version}-#{arch}.dmg"
  name "PwrGit"
  desc "Desktop Git client for managing repositories and worktrees"
  homepage "https://pwrgit.com/"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: :ventura

  app "PwrGit.app"
end
