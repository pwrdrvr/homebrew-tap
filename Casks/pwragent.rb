# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.2.2"
  sha256 arm:   "cb155609ea076e437ac10243fc9c35216c5fed99c6ee072e8526c40a2a11e1cd",
         intel: "4e5d9b16199bbbc5a69a3713599a4b01450096362e6b2720a58f20d77c9c39ff"

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
