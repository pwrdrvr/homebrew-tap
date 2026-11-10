# frozen_string_literal: true

cask "pwragent" do
  arch arm: "arm64", intel: "universal"

  version "1.3.16"
  sha256 arm:   "cdbe13b67f94ad0b914e4e62daa2ec5120f8288f7e7c3ec0eae382897de742c7",
         intel: "602e46abe5cd423957341ab2f8ab87c9553ee587f199890d8f8a050554adfbf8"

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
