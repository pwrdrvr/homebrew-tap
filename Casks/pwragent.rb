# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.4.3"
  sha256 arm:   "510b349b6973367e22729c3315731b54295cbf8ba8de97f1de2b7a2336a8642b",
         intel: "7312ae71b203e7b24fb015be3d8e46ee82db89fc2998fa4603c4deac2e79eea7"

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
