cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.59.4"
  sha256 arm:   "058055bcb34c1b9f7414f5e6f86045dc454f7d3ecbcd407d2dc26d087279f899",
         intel: "d34f3efe38249cd3ff3c9342f311fc3610424383e00b1ec2f6f0b072375ad8cb"

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
