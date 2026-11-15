cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.59.3"
  sha256 arm:   "de974440eb8a3a1b01137916894f313f61402539735bf0857a3c40f5955f847e",
         intel: "154944ce626172536a1b1b2182004a6043ef7ef0bfa0fb40a3ac93ed0d7275c7"

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
