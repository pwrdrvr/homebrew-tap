cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.32.0"
  sha256 arm:   "c6cbf80428dd32b0b35a9b9e96c9825d90440559a122f880d041c23a27406fc0",
         intel: "873131af144d9e46539bcc4346671243141b3789546ba9681ef61f2c40cde602"

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
