# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.3.2"
  sha256 arm:   "4703e4f59588e8a3ece1f43cec2b5bb6ce6e2b482b35e1abb7d125f7cd5859cc",
         intel: "a8d99e2b06eeb8ad30a0a7036883ac833fc3cc49a334d127923bc22b10a929da"

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
