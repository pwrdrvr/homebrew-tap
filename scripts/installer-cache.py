#!/usr/bin/env python3
"""Cache only immutable release installers; verify before seeding Homebrew."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def asset_plan(url, sha256, version, architecture, size=None):
    match = re.fullmatch(
        r"https://github.com/(pwrdrvr/(?:PwrGit|PwrAgent|PwrSnap))/releases/download/"
        r"v([0-9]+(?:\.[0-9]+)+)/([A-Za-z0-9.-]+\.dmg)", url
    )
    if not match or match[2] != version:
        raise ValueError("Expected a version-specific PwrDrvr release DMG")
    if not re.fullmatch(r"[a-f0-9]{64}", sha256):
        raise ValueError("Expected a SHA-256 checksum")
    if architecture not in {"arm64", "universal"}:
        raise ValueError("Expected an installer architecture")
    if not match[3].endswith(f"-{version}-{architecture}.dmg"):
        raise ValueError("Asset version/architecture does not match its URL")
    if size is not None and (not isinstance(size, int) or size <= 0):
        raise ValueError("Expected a positive release size")
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    key = f"tap-installer-v1-{version}-{architecture}-{sha256}-{url_hash}"
    return dict(url=url, sha256=sha256, version=version, architecture=architecture,
                size=size, key=key, path=f".local/installers/{key}.dmg")


def release_asset(url, api=command):
    repo, tag, name = re.fullmatch(
        r"https://github.com/(pwrdrvr/[^/]+)/releases/download/(v[^/]+)/([^/]+)", url
    ).groups()
    release = json.loads(api("gh", "api", f"repos/{repo}/releases/tags/{tag}"))
    matches = [a for a in release["assets"] if a["name"] == name and a["browser_download_url"] == url]
    if len(matches) != 1 or not re.fullmatch(r"sha256:[a-f0-9]{64}", matches[0].get("digest") or ""):
        raise ValueError("Release asset has no unique GitHub SHA-256 digest")
    return matches[0]


def brew_plan(token, api=command):
    cask = json.loads(api("brew", "info", "--json=v2", "--cask", token))["casks"][0]
    url, sha, version = cask["url"], cask["sha256"], cask["version"]
    arch = re.search(r"-(arm64|universal)\.dmg$", url).group(1)
    plan = asset_plan(url, sha, version, arch)
    asset = release_asset(url, api)
    if asset["digest"] != f"sha256:{sha}":
        raise ValueError("Cask checksum differs from the live release digest")
    plan = asset_plan(url, sha, version, arch, asset["size"])
    plan["token"] = token
    return plan


def verify(path, plan):
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if digest.hexdigest() != plan["sha256"] or (plan["size"] is not None and size != plan["size"]):
        raise ValueError(f"Installer digest/size mismatch: {path}")


def ensure(plan, download=subprocess.run):
    path = Path(plan["path"])
    if path.exists():
        verify(path, plan)  # Restored caches are untrusted, even on an exact key.
        return "restored"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial")
    try:
        download(["curl", "-fsSL", "--retry", "3", "-o", str(temporary), plan["url"]], check=True)
        verify(temporary, plan)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return "downloaded"


def seed_brew(plan, api=command):
    verify(plan["path"], plan)
    # Ask Homebrew for its downloader's real cached_location. A generic Cask/
    # directory or a guessed filename will not be reused by audit/install.
    target = Path(api("brew", "--cache", "--cask", plan["token"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(plan["path"], target)
    verify(target, plan)
    print(f"Seeded Homebrew download cache: {target}")


def outputs(plan):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            for key in ["key", "path"]:
                output.write(f"{key}={plan[key]}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "ensure"])
    parser.add_argument("--plan", required=True)
    parser.add_argument("--token", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--sha256", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--architecture", default="")
    parser.add_argument("--size", default="")
    parser.add_argument("--from-release", action="store_true")
    args = parser.parse_args()
    if args.operation == "plan":
        if args.from_release:
            asset = release_asset(args.url)
            args.sha256, args.size = asset["digest"][7:], str(asset["size"])
        plan = brew_plan(args.token) if args.token else asset_plan(
            args.url, args.sha256, args.version, args.architecture, int(args.size) if args.size else None
        )
        Path(args.plan).parent.mkdir(parents=True, exist_ok=True)
        Path(args.plan).write_text(json.dumps(plan))
        outputs(plan)
    else:
        plan = json.loads(Path(args.plan).read_text())
        status = ensure(plan)
        if plan.get("token"):
            seed_brew(plan)
        report = f"Installer {status}: {plan['version']} {plan['architecture']} {plan['sha256']}"
        print(report)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
                summary.write(report + "\n")


if __name__ == "__main__":
    main()
