# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.5.0"
  sha256 arm:   "a3c6632a69662e1a0c5060cc73836986e35f5d39db07fff808b89913e4d8dc2d",
         intel: "0b0cd881a7355ac172bb66020f0f062c752dbe258e2ef4685cb29ccb3a167a55"

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
