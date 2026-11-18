# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.4.10"
  sha256 arm:   "d4d0f949fb8917295969c1fff3a10117bd97cfc3c1629cb479821932368f29bc",
         intel: "7150a9fca2a95e01a3d6205bed8ebfff4a0a7b2885eb10d19b373e9d982f06fd"

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
