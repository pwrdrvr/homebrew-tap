cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.63.0"
  sha256 arm:   "f7bd4d0344c1ccd81664add3b08c9b2bb54467682ffa3ed131d64f06acd490c3",
         intel: "0d22898a6f7b02fc5154ff4a0818249b5aebe64c67d8e2ac2cfac239ef7c8e68"

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
