# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.4.6"
  sha256 arm:   "4d75f2ef4bb3bec4a2246e54408993522a347b7db8308e101450f5c4c139e626",
         intel: "5012eff860f4052c0cc0f1caf2cf9ce2392169b9540afbd2af1da941b50daa01"

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
