cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.54.0"
  sha256 arm:   "901602cdf3af00a118c255871987ae66991b7bbb094748f23b2ee8c10490cd6d",
         intel: "a3081601fee3fbf50a537c57d8e56a22302e3720cdb5f6d409503585a521b25e"

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
