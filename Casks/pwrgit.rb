cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.59.2"
  sha256 arm:   "af3127409d952c5963f901b0319c8d07b70b46c9d495d1ac396d018fefa085a8",
         intel: "23e25b3abbac1ae5c3b2866bec7e9f9ce93ea05147629242e310bd61c8fb8b17"

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
