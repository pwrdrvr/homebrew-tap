# pwrdrvr/homebrew-tap

Homebrew tap for [PwrDrvr LLC](https://pwrdrvr.com) software.

## PwrAgent

[PwrAgent](https://pwragent.ai) is a thread-centric coding agent desktop app.
Its cask selects the signed/notarized arm64 DMG on Apple Silicon and universal
DMG on Intel, from promoted stable [GitHub releases](https://github.com/pwrdrvr/PwrAgent/releases/latest).

```bash
brew install --cask pwrdrvr/tap/pwragent
brew upgrade --cask --greedy pwrdrvr/tap/pwragent
brew uninstall --cask pwrdrvr/tap/pwragent
```

If required, trust only this cask with `brew trust --cask pwrdrvr/tap/pwragent`.
Uninstall preserves `~/.pwragent`, including profiles and thread state.

The [PwrAgent distribution workflow](https://github.com/pwrdrvr/PwrAgent/actions/workflows/package-manager-distribution.yml)
prepares update PRs after stable promotion and daily reconciliation, validates
both macOS architectures and fresh installs/upgrades, and leaves merging to
maintainers. [CI](.github/workflows/ci.yml) checks both casks. Alpha/beta builds
do not change this cask. For the release procedure and credential setup, see
[the PwrAgent distribution runbook](https://github.com/pwrdrvr/PwrAgent/blob/main/docs/package-manager-distribution.md).

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
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) checks cask style,
  online audit, installation, Developer ID signature, Gatekeeper, and
  uninstall on Apple Silicon and Intel macOS runners.
- To bump by hand: `scripts/bump-cask.sh 1.0.4`.

Only the **Stable** train is published here (`/releases/latest`). Alpha
and beta builds are GitHub Pre-releases; opt in from inside the app under
Settings → General → Update channel.

## CI scope

Pull requests validate added or modified `Casks/*.rb` relative to the PR
base's merge ancestor. An unchanged sibling cask is not audited, so its
livecheck drift cannot block another app's registration. Deleted casks
are skipped, and renamed casks are checked under their new token.

App-specific `scripts/bump-<cask>.sh`, `.mjs`, or `.py` and
`.github/workflows/bump-<cask>.yml` or `.yaml` changes also select that
cask. The legacy `scripts/bump-cask.sh` and `bump.yml` select PwrSnap.
Markdown and `docs/` changes do not select casks. Other changes, including
shared CI, selection tests, and tap code, validate all present casks.
Pushes to `main` and manual CI runs also validate all present casks.

New app registrations need no matrix or bundle-name mapping: CI discovers
cask tokens and reads `app` artifacts from Homebrew metadata. Keep shared
CI changes in a separate PR when a registration should validate only its
own cask. Run the selector regression suite with
`python3 -m unittest discover -s tests -v`.

## Why a tap and not `homebrew/cask`?

Homebrew's main cask repository requires a notability threshold (≥ 75
stars or ≥ 30 forks/watchers; 3× that for self-submitted casks). PwrSnap
isn't there yet. This tap has no such gate and works identically for
users — the command is just one token longer. When the repo clears the
bar, the cask moves to `homebrew/cask` and `brew install --cask pwrsnap`
starts working without the tap prefix.

## PwrGit

The `pwrgit` cask uses PwrGit's promoted Stable Latest release, with native
arm64 on Apple Silicon and the universal DMG on Intel:

```sh
brew install --cask pwrdrvr/tap/pwrgit
brew upgrade --cask --greedy pwrdrvr/tap/pwrgit
```

The tap owns publication. `bump-pwrgit.yml` accepts an immediate dispatch after
PwrGit is promoted to Stable Latest and checks Latest every 15 minutes as a
fallback. It downloads both versioned DMGs and checks their sizes and SHA-256
against GitHub, then audits, installs/upgrades, verifies bundle identity,
architectures, Developer ID/Gatekeeper, and uninstalls on Intel and Apple Silicon.
Only after both jobs pass does its own `GITHUB_TOKEN` commit the single validated
cask to `main`. Routine releases require no bump PR, workflow approval or merge.
The publisher rechecks Latest, artifact metadata and the previous cask SHA before
committing; concurrent changes fail rather than overwrite another update.

PwrGit's release workflow uses `HOMEBREW_TAP_DISPATCH_TOKEN` solely to dispatch
this tap workflow: a fine-grained PAT owned by `pwrdrvr`, selected repository
`homebrew-tap`, Actions write permission. The existing public-read-only
`DISTRIBUTION_READ_TOKEN` is used for public reads and cannot dispatch workflows.
No cross-repository contents-write credential is needed. The release skill can
also dispatch using the maintainer's existing GitHub CLI authentication.

This registration PR must be merged once before automatic publication is live.
Scheduling is best effort on GitHub Actions; immediate dispatch is the normal
promotion path. Failed runs file one tracking issue per outage with a direct run
link. The product release workflow waits for the cask to appear on tap `main`
and reports a direct run link on failure. Check the default branch and refresh
Homebrew before declaring client discovery/install verified.

After merge run `brew update`, inspect `brew info --cask pwrdrvr/tap/pwrgit`
and test installation before describing the version as live. The cask retains
all user data on uninstall and deliberately has no `zap` stanza. Publication failures
open one tracking issue per outage with the failed run and a recovery action.
