# Maintaining the tap

The tap publishes stable macOS releases of [PwrAgent](https://pwragent.ai),
[PwrSnap](https://pwrsnap.com), and [PwrGit](https://pwrgit.com). Alpha and beta builds do not update these
casks.

## PwrAgent releases

[`Casks/pwragent.rb`](../Casks/pwragent.rb) selects the signed/notarized arm64 DMG on Apple Silicon
and universal DMG on Intel from promoted stable
[GitHub releases](https://github.com/pwrdrvr/PwrAgent/releases/latest).

The [PwrAgent distribution workflow](https://github.com/pwrdrvr/PwrAgent/actions/workflows/package-manager-distribution.yml)
prepares update PRs after stable promotion and daily reconciliation, validates
both macOS architectures and fresh installs/upgrades, and leaves merging to
maintainers. For the release procedure and credential setup, see
[the PwrAgent distribution runbook](https://github.com/pwrdrvr/PwrAgent/blob/main/docs/package-manager-distribution.md).

## PwrSnap releases

- [`Casks/pwrsnap.rb`](../Casks/pwrsnap.rb) pins a `version` + `sha256` of
  `PwrSnap-<version>-universal.dmg`.
- [`.github/workflows/bump.yml`](../.github/workflows/bump.yml) checks
  `pwrdrvr/PwrSnap`'s latest stable release every six hours (or on
  demand with a version input), re-hashes the DMG, runs `brew style` +
  `brew audit --cask --online`, and opens a PR.
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) checks cask style,
  online audit, installation, Developer ID signature, Gatekeeper, and
  uninstall on Apple Silicon and Intel macOS runners.
- To bump by hand, run `scripts/bump-cask.sh <version>` from the repository root.

Only the **Stable** train is published here (`/releases/latest`). Alpha
and beta builds are GitHub Pre-releases; opt in from inside the app under
Settings → General → Update channel.

## PwrGit releases

[`Casks/pwrgit.rb`](../Casks/pwrgit.rb) uses PwrGit's promoted Stable Latest
release, with native arm64 on Apple Silicon and the universal DMG on Intel.

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

## README screenshots

The screenshots in [assets](assets/) are copies of the product websites' hero
images, kept in this repository so the README does not depend on remote image
hosting:

- [PwrAgent](https://pwragent.ai/assets/screenshots/desktop-hero.png) → `assets/pwragent.png`
- [PwrSnap](https://pwrsnap.com/assets/screenshots/desktop-hero.png) → `assets/pwrsnap.png`
- [PwrGit](https://pwrgit.com/assets/screenshots/hero.png) → `assets/pwrgit.png`

When refreshing them, use real app screenshots and keep the README's descriptive
alt text and links to the product websites.
