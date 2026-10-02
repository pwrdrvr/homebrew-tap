cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.27.0"
  sha256 arm:   "a6043c1fa1d1463951eb380d72ac5571115ca61ea72786218fea37e4343bddb6",
         intel: "2044a11927082bf6a82190a3490c2f363e93d0343201a637175458339b2d2164"

  url "https://github.com/pwrdrvr/PwrGit/releases/download/v#{version}/PwrGit-#{version}-#{arch}.dmg"
  name "PwrGit"
  desc "Desktop Git client for managing repositories and worktrees"
  homepage "https://pwrgit.com/"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: :monterey

  app "PwrGit.app"
end
