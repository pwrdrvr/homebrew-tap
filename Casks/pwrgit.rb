cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.51.0"
  sha256 arm:   "78570493ee137735a26673b6ddbb6ed75f1acd9b4fb8df74a4fe782386442826",
         intel: "5f103877cf9f5f04ea6f3b572aeb497c0e1e7604e07f06af1cc247333614802b"

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
