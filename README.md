<div align="center">

<h1>PwrDrvr apps for your Mac</h1>

<strong>Run coding agents. Capture what matters. Keep moving.</strong>

<p>Free, open-source desktop apps from <a href="https://pwrdrvr.com">PwrDrvr</a>.<br>
MIT licensed. Signed and notarized. One command to install.</p>

</div>

Have [Homebrew](https://brew.sh)? Pick an app below and paste its install command into your terminal.

---

## [PwrAgent](https://pwragent.ai)

**Run coding agents by the dozen.**

Keep agents working across your repos, each in its own git worktree.
Watch the diffs, track the PRs, and steer your threads from your desktop or
your favorite messenger. Use the coding-agent CLI and plan you already have.

[![PwrAgent desktop with threads grouped by repository, an active coding conversation, and model and worktree controls](docs/assets/pwragent.png)](https://pwragent.ai)

**Install PwrAgent**

```bash
brew install --cask pwrdrvr/tap/pwragent
```

macOS 12 Monterey or newer · Apple Silicon + Intel

[Explore PwrAgent](https://pwragent.ai) · [Documentation](https://docs.pwragent.ai) · [Source code](https://github.com/pwrdrvr/PwrAgent)

---

## [PwrSnap](https://pwrsnap.com)

**Screen capture for the agent age.**

Capture screenshots and screen recordings, annotate them, and find them again
in a library organized by source app. Copy at the resolution you need, or
bring in optional AI through the agent install you already use.

[![PwrSnap Library with captures grouped by source app, a screenshot grid, and one-click copy options at multiple resolutions](docs/assets/pwrsnap.png)](https://pwrsnap.com)

**Install PwrSnap**

```bash
brew install --cask pwrdrvr/tap/pwrsnap
```

macOS 14 Sonoma or newer · Apple Silicon + Intel

[Explore PwrSnap](https://pwrsnap.com) · [Documentation](https://docs.pwrsnap.com) · [Source code](https://github.com/pwrdrvr/PwrSnap)

---

## [PwrGit](https://pwrgit.com)

**Git for people working alongside an agent.**

Keep your repositories and worktrees together in one window. See how branches
connect in the lineage graph, review changes, and track pull and merge requests
without losing your place while agents work alongside you.

[![PwrGit desktop with repositories and worktrees in the sidebar, a branch lineage graph, and changes for the selected worktree](docs/assets/pwrgit.png)](https://pwrgit.com)

**Install PwrGit**

```bash
brew install --cask pwrdrvr/tap/pwrgit
```

macOS 13 Ventura or newer · Apple Silicon + Intel

[Explore PwrGit](https://pwrgit.com) · [Documentation](https://docs.pwrgit.com) · [Source code](https://github.com/pwrdrvr/PwrGit)

---

<details>
<summary>Updates, uninstalling, and Homebrew trust</summary>

All three apps update themselves. To update through Homebrew, run the command for your app:

```bash
brew upgrade --cask --greedy pwrdrvr/tap/pwragent
```

```bash
brew upgrade --cask --greedy pwrdrvr/tap/pwrsnap
```

```bash
brew upgrade --cask --greedy pwrdrvr/tap/pwrgit
```

To uninstall:

```bash
brew uninstall --cask pwrdrvr/tap/pwragent
```

```bash
brew uninstall --cask pwrdrvr/tap/pwrsnap
```

```bash
brew uninstall --cask pwrdrvr/tap/pwrgit
```

PwrGit preserves all user data on uninstall.
PwrAgent preserves `~/.pwragent`, including profiles and thread state.
For PwrSnap, adding `--zap` also removes settings, caches, and logs; your
captures in `~/Documents/PwrSnap` are preserved.

If Homebrew reports an untrusted cask, trust the app you are installing:

```bash
brew trust --cask pwrdrvr/tap/pwragent
```

```bash
brew trust --cask pwrdrvr/tap/pwrsnap
```

```bash
brew trust --cask pwrdrvr/tap/pwrgit
```

</details>

[Maintaining this tap](docs/maintenance.md) · [About PwrDrvr](https://pwrdrvr.com/about)
