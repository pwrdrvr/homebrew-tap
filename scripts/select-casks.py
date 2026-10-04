#!/usr/bin/env python3
"""Select casks for CI without querying any app's live release metadata."""

import argparse
import json
import re
import subprocess
from pathlib import PurePosixPath


def git_paths(*args):
    result = subprocess.run(
        ["git", *args], check=True, stdout=subprocess.PIPE
    )
    return result.stdout.decode().rstrip("\0").split("\0") if result.stdout else []


def cask_token(path):
    match = re.fullmatch(r"Casks/([a-z0-9][a-z0-9+_.@-]*)\.rb", path)
    return match.group(1) if match else None


def bump_token(path, present):
    # Historical PwrSnap names predate the per-app bump convention.
    if path in {"scripts/bump-cask.sh", ".github/workflows/bump.yml"}:
        return "pwrsnap" if "pwrsnap" in present else None
    match = re.fullmatch(
        r"(?:scripts/bump-([^/]+)\.(?:sh|mjs|py)|"
        r"\.github/workflows/bump-([^/]+)\.ya?ml)", path
    )
    if match:
        token = match.group(1) or match.group(2)
        return token if token in present else None
    return None


def select_casks(event, base=None):
    present = sorted(
        token
        for path in git_paths("ls-tree", "-r", "--name-only", "-z", "HEAD", "--", "Casks")
        if (token := cask_token(path))
    )
    if event == "workflow_dispatch":
        return {"casks": present, "reason": f"{event}: all present casks"}
    if not base or re.fullmatch(r"0+", base):
        # A newly-created main has no previous commit. Fail closed for missing
        # event data; only GitHub's explicit zero SHA means the whole tree is new.
        if event == "push" and base and re.fullmatch(r"0+", base):
            return {"casks": present, "reason": "push: new branch"}
        raise ValueError(f"{event} selection requires a base commit")

    # Three-dot diff ignores changes made only on the base branch. Disable
    # rename detection so a renamed cask is selected under its new token.
    # Pushes use the exact before/after range, including multi-commit pushes
    # and force pushes. PRs compare to the merge base instead.
    revision = f"{base}...HEAD" if event == "pull_request" else f"{base}..HEAD"
    changed = git_paths("diff", "--name-only", "--no-renames", "-z", revision)
    selected = set()
    for path in changed:
        token = cask_token(path)
        if token:
            if token in present:
                selected.add(token)
            continue  # Deleted casks cannot be installed.
        token = bump_token(path, present)
        if token:
            selected.add(token)
            continue
        if PurePosixPath(path).suffix == ".md" or path.startswith("docs/"):
            continue
        # Unknown code/configuration is conservatively shared. In particular,
        # ci.yml, this selector, tests, and shared tap code validate every cask.
        return {"casks": present, "reason": f"shared change: {path}"}
    return {"casks": sorted(selected), "reason": "changed casks and app-specific bump files"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, choices=["pull_request", "push", "workflow_dispatch"])
    parser.add_argument("--base")
    args = parser.parse_args()
    try:
        print(json.dumps(select_casks(args.event, args.base)))
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Cask selection failed: {error}\n")


if __name__ == "__main__":
    main()
