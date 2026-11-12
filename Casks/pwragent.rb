# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.4.0"
  sha256 arm:   "de521271272b349a5ca9fc585b17e39e8a461ea7e0825d49421a655aa42bc5ab",
         intel: "5fd6255fe1b42d2496721dfe70c1ba053ac71166358e1be67644bc929174721e"

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
