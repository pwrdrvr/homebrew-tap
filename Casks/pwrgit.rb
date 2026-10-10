cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.35.0"
  sha256 arm:   "92f8cf64f86e23a29023ee6b12231716564437d48d0ee9c729e6c31af4704fb0",
         intel: "a451f35a721b93a3bac708d48dde11b123b3e789283f4d4feb108908311ce15e"

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
