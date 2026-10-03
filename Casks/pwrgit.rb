cask "pwrgit" do
  arch arm: "arm64", intel: "universal"

  version "0.29.0"
  sha256 arm:   "a9a344946551d259d4ba24cf8e30b072bb25201bd01d93695871f510c1ddd92a",
         intel: "3af710e6c2870a8468e3d73104cf49ce76c8a7d09403ae19413cb52a4683d91d"

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
