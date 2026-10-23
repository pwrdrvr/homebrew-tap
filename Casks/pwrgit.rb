cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.40.0"
  sha256 arm:   "101ac8ac9811a7fc3aea604b1e226ba662b8ddbfff2fb9ff64ee76abc287a341",
         intel: "93afc7739057db8e0eaa160a054118e67ae36a4d8f931483a047a2178077007c"

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
