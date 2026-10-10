# Maintaining the tap

The tap publishes stable macOS releases of [PwrAgent](https://pwragent.ai),
[PwrSnap](https://pwrsnap.com), and [PwrGit](https://pwrgit.com). Alpha and beta builds do not update these
casks.

## Stable release publication

The tap owns automatic publication for all three apps. `bump-pwrgit.yml`,
`bump.yml` (PwrSnap), and `bump-pwragent.yml` each accept a manual version input
and check Stable Latest every 15 minutes. They call `sync.yml`, which validates
both native Mac profiles and commits the validated cask directly to `main`.
Routine releases require no bump PR or merge approval. Product workflows can
immediately dispatch using `HOMEBREW_TAP_DISPATCH_TOKEN` (tap-only Actions write);
without it, they await the independent tap schedule. Public-read credentials and
Winget submission credentials remain separate.

Installer acquisition uses retained **Actions build artifacts**, never published
release-download URLs. The resolver requires a successful `release.yml` run for
the exact stable tag commit, rejects PR/fork/preview/failed runs, and verifies each
member's SHA-256 and size against GitHub release metadata. Existing signed
macOS/Windows artifacts retain for 90 days in the product workflows. The tap's
installer cache stores exact verified bytes; restored bytes are checked again.
A Homebrew curl guard prohibits PwrDrvr release-asset requests, so a missing
cache step cannot silently increase release download statistics.

Missing/expired artifacts, corrupt bytes, moved tags, changed release metadata,
or concurrent cask edits stop publication and file one tracking issue per outage.
Restore the original build artifacts or repair the failed step, then dispatch the
app's tap workflow on `main`. Never rebuild a published installer or substitute
release downloads to make validation pass. Already published versions are
immutable no-ops even when caches expire or validation code changes.

The updater reads the tagged release's minimum macOS requirement. Native checks
cover the prior published installation, upgrade, fresh candidate installation,
app identity/version/minimum OS, architecture, Developer ID, Gatekeeper, stapled
notarization, and uninstall. PwrGit/PwrAgent use arm64 on Apple Silicon and
universal on Intel; PwrSnap preserves its universal cask. Uninstall preserves
user data, and PwrSnap's existing explicit zap list remains unchanged.

Publication rechecks Stable Latest, installer identity, the tag commit and the
previous cask blob before writing. After publication, refresh Homebrew and verify
client discovery with `brew update` and `brew info --cask pwrdrvr/tap/<app>`.
Do not replace an operator's running application for a smoke test; native install
and upgrade validation runs on isolated hosted CI runners.

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
