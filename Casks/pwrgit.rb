cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.59.5"
  sha256 arm:   "95448de6e8c9cc541781905a884fc4c33b30470626da05820b4d165c3734ce28",
         intel: "33886ec7d38650a83e9b84dad9c5e46fb7c9cc370a62adc77ebfc0b3fdf00fff"

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
