cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.58.0"
  sha256 arm:   "c6a4aac5a7c0e70e9c770d5ca858f871bea55201e1a0db9c753acaf02c4ce1aa",
         intel: "ed7eab8d6d9410cdf913a29c7f52467abf58b3a5024f672bc6586c17262fb21f"

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
