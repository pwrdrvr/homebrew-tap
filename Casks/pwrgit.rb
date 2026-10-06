cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.30.0"
  sha256 arm:   "a62b514c8f1d060c93388e39635a183790936b69d74abec1492f771cfb14f099",
         intel: "3f75bbe9a1234cccc62be83f9bfd5830ee7add60a6a3d3cf1d5c5fdb26d7a9db"

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
