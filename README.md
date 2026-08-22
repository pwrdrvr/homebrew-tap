# pwrdrvr/homebrew-tap

Homebrew tap for [PwrDrvr LLC](https://pwrdrvr.com) software.

## PwrSnap

[PwrSnap](https://pwrsnap.com) — open-source screen capture, annotation,
and screen recording for macOS and Windows, with optional AI assist that
rides the Codex install you already have. MIT licensed.

```bash
brew install --cask pwrdrvr/tap/pwrsnap
```

That one-liner taps this repository and installs the signed, notarized
universal DMG from [GitHub Releases](https://github.com/pwrdrvr/PwrSnap/releases/latest).
First launch is one double-click — no "unidentified developer" warning.

### If Homebrew says the tap isn't trusted

Homebrew 6.0 (June 2026) added [tap trust](https://docs.brew.sh/Tap-Trust):
non-official taps must be trusted before Homebrew will load their Ruby.
Read-only operations against this cask work untrusted on current 6.0.x,
and the one-liner above is exercised on a clean macOS runner by
[CI](.github/workflows/ci.yml) on every PR — but if you ever see
`Not trusted cask` or a "the following taps are not trusted" warning:

```bash
brew trust --cask pwrdrvr/tap/pwrsnap
```

Trust the single cask, not the whole tap — whole-tap trust also covers
every future formula, cask, and command added here. (Official taps such
as `homebrew/cask` need no trust at all, which is one more reason to
move this cask there once PwrSnap clears the notability bar.)

Updating:

```bash
brew upgrade --cask pwrsnap
```

PwrSnap also updates itself (Settings → General → Check for Updates), so
the cask is marked `auto_updates true` — Homebrew won't complain when the
app is ahead of the tap.

Uninstall (`--zap` also removes settings, caches, and logs; it never
touches your captures in `~/Documents/PwrSnap`):

```bash
brew uninstall --cask pwrsnap
brew uninstall --cask --zap pwrsnap
```

## How the cask stays current

- `Casks/pwrsnap.rb` pins a `version` + `sha256` of
  `PwrSnap-<version>-universal.dmg`.
- [`.github/workflows/bump.yml`](.github/workflows/bump.yml) checks
  `pwrdrvr/PwrSnap`'s latest stable release every six hours (or on
  demand with a version input), re-hashes the DMG, runs `brew style` +
  `brew audit --cask --online`, and opens a PR.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) installs the
  cask on a macOS runner and checks the Developer ID signature before a
  PR can merge.
- To bump by hand: `scripts/bump-cask.sh 1.0.4`.

Only the **Stable** train is published here (`/releases/latest`). Alpha
and beta builds are GitHub Pre-releases; opt in from inside the app under
Settings → General → Update channel.

## Why a tap and not `homebrew/cask`?

Homebrew's main cask repository requires a notability threshold (≥ 75
stars or ≥ 30 forks/watchers; 3× that for self-submitted casks). PwrSnap
isn't there yet. This tap has no such gate and works identically for
users — the command is just one token longer. When the repo clears the
bar, the cask moves to `homebrew/cask` and `brew install --cask pwrsnap`
starts working without the tap prefix.
