#!/usr/bin/env python3
"""Reuse successful native validation only for the same bytes, code and runner."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlencode

PROFILES = [("macos-26", "arm64"), ("macos-15-intel", "x86_64")]


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def validation_key(token, cask, assets, code, runner, architecture, namespace="tap-validation-v1"):
    identity = dict(cask=cask, assets=assets, code=code, runner=runner, architecture=architecture)
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return f"{namespace}-{token}-{runner}-{architecture}-{digest}"


def release_identity(cask, release):
    tag = re.search(r'^  version "([^"]+)"$', cask, re.M)[1]
    if release["tag_name"] != f"v{tag}" or release.get("draft"):
        raise ValueError("Release does not match the cask version")
    # Include the versioned DMGs, never aliases or mutable download counters.
    # A replacement changes this identity even when the version stays the same.
    assets = [a for a in release["assets"] if re.fullmatch(rf"[^/]+-{re.escape(tag)}-(arm64|universal)\.dmg", a["name"])]
    if not assets:
        raise ValueError("No versioned release installers")
    return [{k: a[k] for k in ["name", "id", "updated_at", "digest", "size", "browser_download_url"]}
            for a in sorted(assets, key=lambda a: a["name"])]


def known_success(key, caches, allowed_refs):
    # The API's key filter is a PREFIX match; never accept a longer/different key.
    # GitHub cannot promote a PR/sibling cache to a trusted main run.
    return any(c["key"] == key and c["ref"] in allowed_refs for c in caches)


def make_matrix(casks, source, release, code, cache_lookup, allowed_refs, force=False, namespace="tap-validation-v1"):
    matrix, reused = [], []
    for token in casks:
        cask = source(token)
        assets = release_identity(cask, release(token, cask))
        for runner, arch in PROFILES:
            key = validation_key(token, cask, assets, code, runner, arch, namespace)
            row = dict(cask=token, os=runner, key=key)
            if not force and known_success(key, cache_lookup(key), allowed_refs):
                reused.append(row)
            else:
                matrix.append(row)
    return dict(include=matrix), reused


def validation_code(sync=False):
    # Only tracked sources: running Python tests must not fingerprint pycache or
    # generated plans. Documentation and unrelated app bump code need no install.
    sources = [".github/workflows/ci.yml", ".github/actions", "scripts/select-casks.py",
               "scripts/installer-cache.py", "scripts/validation-plan.py", "tests"]
    if sync:
        sources.extend([".github/workflows/bump-pwrgit.yml", "scripts/*pwrgit*"])
    paths = command("git", "ls-files", "-z", *sources).split("\0")
    digest = hashlib.sha256()
    for path in sorted(p for p in paths if p):
        digest.update(path.encode() + b"\0" + Path(path).read_bytes() + b"\0")
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selection")
    mode.add_argument("--pwrgit-sync", metavar="DIRECTORY")
    args = parser.parse_args()
    selected = ["pwrgit"] if args.pwrgit_sync else json.loads(Path(args.selection).read_text())["casks"]
    repo = os.environ.get("GITHUB_REPOSITORY", "pwrdrvr/homebrew-tap")
    refs = {"refs/heads/main", os.environ.get("GITHUB_REF", ""), "refs/heads/" + os.environ.get("BASE_REF", "main")}
    def release(token, cask):
        owner_repo = re.search(r'url "https://github.com/(pwrdrvr/[^/]+)/releases/download/', cask)[1]
        tag = re.search(r'^  version "([^"]+)"$', cask, re.M)[1]
        return json.loads(command("gh", "api", f"repos/{owner_repo}/releases/tags/v{tag}"))
    def cache_lookup(key):
        entries = []
        for ref in sorted(r for r in refs if r):
            query = urlencode(dict(key=key, ref=ref, per_page=100))
            lines = command("gh", "api", "--paginate", f"repos/{repo}/actions/caches?{query}",
                            "--jq", '.actions_caches[] | {key,ref} | @json')
            entries.extend(json.loads(line) for line in lines.splitlines())
        return entries
    code = validation_code(sync=bool(args.pwrgit_sync))
    source = lambda token: Path(f"Casks/{token}.rb").read_text()
    namespace = "tap-validation-v1"
    if args.pwrgit_sync:
        previous = source("pwrgit")
        prior_assets = release_identity(previous, release("pwrgit", previous))
        code = json.dumps(dict(code=code, previous_cask=previous, previous_assets=prior_assets), sort_keys=True)
        source = lambda token: (Path(args.pwrgit_sync) / "Casks/pwrgit.rb").read_text()
        release = lambda *args: json.loads((Path(args.pwrgit_sync) / "release.json").read_text())
        namespace = "tap-sync-validation-v1"
    matrix, reused = make_matrix(selected, source, release, code, cache_lookup, refs,
                                 force=os.environ.get("FORCE_VALIDATION") == "true", namespace=namespace)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"matrix={json.dumps(matrix, separators=(',', ':'))}\n")
    report = f"Native validations required: {len(matrix['include'])}; identical successful validations reused: {len(reused)}"
    print(report)
    print(json.dumps(dict(matrix=matrix, reused=reused)))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(report + "\n")


if __name__ == "__main__":
    main()
