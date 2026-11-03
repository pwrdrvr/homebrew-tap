cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.50.0"
  sha256 arm:   "44b56f0d7b6f1fac9725941dd93cb048a26a5c785eea265c37d805086cb4cbfb",
         intel: "a08a3944ee7d3de971e3b404051e9c70df5bd64aeddd230544d74c9483aa40e3"

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
