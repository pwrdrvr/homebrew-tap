cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.60.0"
  sha256 arm:   "4439a442ab949768965432dec4fad9fbad5a20e299ed58f53ccbbcb4be5724f4",
         intel: "66511dd8583bc9316816de4d546f5c10d0faba5f310e4cb31991fd1c032b1e7c"

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
  command_wrapper "pwrgit", executable: "#{appdir}/PwrGit.app/Contents/Resources/git/bin/git"
end
