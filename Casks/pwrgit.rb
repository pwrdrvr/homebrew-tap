cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.61.3"
  sha256 arm:   "741d11a55a069fc27e8e0706659c09815e6359240b3c4bff695c072458713b47",
         intel: "0f198c0dc15e4b21adae60386a45a297876638a1e3d484ccd7132d3bb1206b7d"

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
