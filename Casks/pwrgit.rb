cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.38.0"
  sha256 arm:   "4dec1db2b537368406f51cfa95d9ab9034be9c4db808644ea75cf96edf9afd9c",
         intel: "1b406790a83e9cb1720d0a077c2d14c186bd744fb70dd829ecef9ced82be95b9"

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
