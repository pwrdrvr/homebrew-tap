cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.45.0"
  sha256 arm:   "52e847559e9a337d0085cf727935d199ea59a1b1df3bd682ceae237dce82432f",
         intel: "babd2da077219c6c79f0524610735a045797406740451b04ff82743dc12f9ebd"

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
