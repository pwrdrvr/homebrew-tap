cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.57.0"
  sha256 arm:   "a8118bdd4b117d9d4f21d3c385a92a76c411bb8b076b8f220f87b35eda4a8cdf",
         intel: "79c889a2877ee408c2dfd01f8423b2439403d5355bcb769f265c08e2a7f14b35"

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
