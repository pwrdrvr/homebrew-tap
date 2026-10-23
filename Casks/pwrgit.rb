cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.41.0"
  sha256 arm:   "826a2f924bf13308f289c0e5c01854f366b1ddb0277f938d15efc2eab7abe865",
         intel: "ec87102211c865b782ebadc719334741d991ecc3d0bb294555cb3f9741307825"

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
