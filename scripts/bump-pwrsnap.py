#!/usr/bin/env python3
"""Resolve a PwrSnap candidate and detect an identical, validated pending PR."""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def version(text):
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", text):
        raise ValueError(f"Not a dotted numeric version: {text!r}")
    return tuple(map(int, text.split(".")))


def candidate(current, release, requested=""):
    match = re.search(r'^  version "([^"]+)"$', current, re.M)
    if not match:
        raise ValueError("Cannot read PwrSnap cask version")
    previous = match[1]
    old = version(previous)
    latest = release["tag_name"].removeprefix("v")
    new = version(latest)
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Expected a stable release")
    if requested and requested.removeprefix("v") != latest:
        raise ValueError("Requested version does not match resolved release")
    if latest == previous:
        # Published versions are immutable. Metadata changes or missing caches
        # must never turn the periodic version check into an installer fetch.
        return dict(current=previous, latest=latest, version=previous, changed=False,
                    reason="Version already published; assuming immutable installers")
    if not requested and new < old:
        return dict(current=previous, latest=latest, version=previous, changed=False,
                    reason="Holding newer cask while a maintenance release is Latest")
    name = f"PwrSnap-{latest}-universal.dmg"
    url = f"https://github.com/pwrdrvr/PwrSnap/releases/download/v{latest}/{name}"
    assets = [a for a in release["assets"] if a["name"] == name and a["browser_download_url"] == url]
    if len(assets) != 1 or not re.fullmatch(r"sha256:[a-f0-9]{64}", assets[0].get("digest") or ""):
        raise ValueError("Expected one versioned universal DMG with a GitHub SHA-256 digest")
    asset = assets[0]
    if asset["size"] <= 0:
        raise ValueError("Empty release asset")
    sha = asset["digest"][7:]
    cask, count = re.subn(r'^  sha256 "[a-f0-9]{64}"$', f'  sha256 "{sha}"', current, flags=re.M)
    if count != 1:
        raise ValueError("Unexpected PwrSnap checksum stanza")
    cask = re.sub(r'^  version "[^"]+"$', f'  version "{latest}"', cask, flags=re.M)
    # These fields identify immutable bytes; traffic counters are deliberately excluded.
    identity = {key: asset[key] for key in ["id", "updated_at", "size", "digest", "browser_download_url"]}
    return dict(current=previous, latest=latest, version=latest, changed=cask != current,
                cask=cask, asset=identity, sha256=sha, url=url, size=asset["size"],
                reason="Explicit rollback" if new < old else "Resolved stable release")


def validation_key(plan, validator_hash):
    content = json.dumps(dict(cask=plan["cask"], asset=plan["asset"], validator=validator_hash), sort_keys=True)
    return "pwrsnap-validation-v1-macos-26-arm64-" + hashlib.sha256(content.encode()).hexdigest()


def pending_matches(plan, pulls, read_cask, read_files):
    branch = f"bump/pwrsnap-{plan['version']}"
    for pr in pulls:
        if (pr["state"] == "open" and pr["base"]["ref"] == "main" and
                pr["head"]["ref"] == branch and
                (pr["head"].get("repo") or {}).get("full_name") == "pwrdrvr/homebrew-tap"):
            files = read_files(pr)
            # An edited PR's scripts/workflows must not inherit a main-branch
            # audit record merely because its cask still looks identical.
            expected_files = all(path == "Casks/pwrsnap.rb" or path.endswith(".md") or path.startswith("docs/") for path in files)
            if expected_files and read_cask(pr["head"]["sha"]) == plan["cask"]:
                return True
    return False


def skip_validation(plan, marker):
    return bool(plan.get("pending") and marker == plan.get("key"))


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def output(values):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as target:
            for key, value in values.items():
                target.write(f"{key}={str(value).lower() if isinstance(value, bool) else value}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "decide", "mark"])
    args = parser.parse_args()
    directory = Path(".local/pwrsnap-candidate")
    marker = Path(".local/validation/pwrsnap/key")
    if args.operation == "plan":
        requested = os.environ.get("REQUESTED", "").removeprefix("v")
        if requested:
            version(requested)  # Reject newlines/output injection before constructing an API path.
        endpoint = f"tags/v{requested}" if requested else "latest"
        plan = candidate(Path("Casks/pwrsnap.rb").read_text(), api(f"repos/pwrdrvr/PwrSnap/releases/{endpoint}"), requested)
        plan["pending"] = False
        if plan["changed"]:
            plan["key"] = validation_key(plan, os.environ["VALIDATOR_HASH"])
            branch = f"bump/pwrsnap-{plan['version']}"
            pulls = api(f"repos/pwrdrvr/homebrew-tap/pulls?state=open&head=pwrdrvr:{branch}&base=main")
            def read_cask(sha):
                result = api(f"repos/pwrdrvr/homebrew-tap/contents/Casks/pwrsnap.rb?ref={sha}")
                return base64.b64decode(result["content"]).decode()
            def read_files(pr):
                files = api(f"repos/pwrdrvr/homebrew-tap/pulls/{pr['number']}/files?per_page=100")
                # Large unexpected PRs are never the simple automated candidate.
                return [f["filename"] for f in files] if len(files) < 100 else ["unexpected-large-pr"]
            plan["pending"] = pending_matches(plan, pulls, read_cask, read_files)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "pwrsnap.rb").write_text(plan["cask"])
            (directory / "plan.json").write_text(json.dumps(plan))
        output({k: plan.get(k, "") for k in ["version", "current", "latest", "changed", "key"]})
        report = f"PwrSnap: tap={plan['current']}, target={plan['version']}, changed={plan['changed']}. {plan['reason']}"
    else:
        plan = json.loads((directory / "plan.json").read_text())
        if args.operation == "decide":
            skip = skip_validation(plan, marker.read_text() if marker.exists() else "")
            output(dict(required=not skip))
            report = "Identical validated candidate is pending; no installer or Mac job needed" if skip else "Candidate requires validation"
        else:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(plan["key"])
            report = "Recorded successful candidate audit and PR publication"
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(report + "\n")


if __name__ == "__main__":
    main()
