# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.3.8"
  sha256 arm:   "96eca56aa1a4df750022994879987aa1d0d421dfb8b460d23dbab983c41d9ac4",
         intel: "53f15b2cbcdfa5a585a01d8850a19c20dc5e97510c76547df40cf86d3b45ed7e"

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
