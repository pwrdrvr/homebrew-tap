cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.47.0"
  sha256 arm:   "56f65f971364ea17758c50628f5ee5c02359257b5fbe61fd5bc64f222a593f19",
         intel: "be6561f8e6e0dcaad8881369d4710cd2df4e82803bee8cd9044025520ac9b968"

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
