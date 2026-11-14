cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.59.1"
  sha256 arm:   "c696a708227fdf15b9d99e9b05481797a605e3438f4a3b6c2341c300d830ac32",
         intel: "8300453ba1783e98674954b5cba4186e000ead8794f86eb773f9d66a6ce84299"

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
