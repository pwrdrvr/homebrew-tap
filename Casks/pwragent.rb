# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.5.1"
  sha256 arm:   "cd7a5e8214585297d2dc0fa1d924dd5cba84e8232bc1aae58fa13b18ed4c6feb",
         intel: "06cff45b27108ad528eca58ed23e32b11e2c2872682fb7b8ae269602632a8ecc"

  url "https://github.com/pwrdrvr/PwrAgent/releases/download/v#{version}/PwrAgent-#{version}-#{arch}.dmg"
  name "PwrAgent"
  desc "Thread-centric coding agent desktop app"
  homepage "https://pwragent.ai/"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: :ventura

  app "PwrAgent.app"

  # Preserve ~/.pwragent: it contains profiles, secrets and thread state.
end
