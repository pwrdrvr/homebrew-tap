#!/usr/bin/env python3
"""Plan and publish stable casks after artifact-backed native validation."""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import importlib.util
from pathlib import Path

APPS = {"pwrgit": "PwrGit", "pwrsnap": "PwrSnap", "pwragent": "PwrAgent"}
spec = importlib.util.spec_from_file_location("build_artifact", Path(__file__).with_name("build-artifact.py"))
artifact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact)
MACOS = {"12": "monterey", "13": "ventura", "14": "sonoma", "15": "sequoia", "26": "tahoe"}


def set_macos(candidate, config):
    floors = re.findall(r'^ *LSMinimumSystemVersion: *"?([0-9]+\.[0-9]+)"? *$', config, re.M)
    if len(floors) != 1 or floors[0].split(".")[0] not in MACOS:
        raise ValueError("Cannot resolve release's minimum macOS version")
    candidate["minimum_os"] = floors[0]
    cask, count = re.subn(r'^  depends_on macos: :[a-z]+$',
                         f'  depends_on macos: :{MACOS[floors[0].split(".")[0]]}', candidate["cask"], flags=re.M)
    if count != 1:
        raise ValueError("Unexpected macOS requirement stanza")
    candidate["cask"] = cask


def api(endpoint, payload=None):
    args = ["gh", "api", endpoint]
    if payload is not None:
        args.extend(["--method", "PUT", "--input", "-"])
    return json.loads(subprocess.check_output(args, input=json.dumps(payload) if payload else None, text=True))


def version(cask):
    match = re.search(r'^  version "(\d+\.\d+\.\d+)"$', cask, re.M)
    if not match:
        raise ValueError("Cannot read stable cask version")
    return match[1]


def assets_for(token, release):
    app = APPS[token]
    target = release["tag_name"][1:]
    arches = ["universal"] if token == "pwrsnap" else ["arm64", "universal"]
    assets = []
    for arch in arches:
        name = f"{app}-{target}-{arch}.dmg"
        url = f"https://github.com/pwrdrvr/{app}/releases/download/v{target}/{name}"
        matches = [asset for asset in release["assets"] if asset["name"] == name]
        if (len(matches) != 1 or matches[0]["browser_download_url"] != url
                or not re.fullmatch(r"sha256:[a-f0-9]{64}", matches[0].get("digest") or "")
                or matches[0]["size"] <= 0):
            raise ValueError(f"Invalid immutable release metadata: {name}")
        assets.append({key: matches[0][key] for key in ["name", "browser_download_url", "digest", "size", "id"]})
    return assets


def plan(token, current, release, requested=""):
    tag = release["tag_name"]
    if release["draft"] or release["prerelease"] or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Expected promoted Stable Latest")
    target, previous = tag[1:], version(current)
    if requested and requested != target:
        raise ValueError("Requested version is no longer Stable Latest")
    if tuple(map(int, previous.split("."))) > tuple(map(int, target.split("."))):
        raise ValueError("Refusing cask downgrade")
    blob = f"blob {len(current.encode())}\0".encode() + current.encode()
    result = dict(token=token, version=target, previous=previous, changed=target != previous,
                  baseSha=hashlib.sha1(blob).hexdigest(), assets=[], cask=current)
    if not result["changed"]:
        return result
    assets = assets_for(token, release)
    cask = re.sub(r'^  version "[^"]+"$', f'  version "{target}"', current, flags=re.M)
    if token == "pwrsnap":
        cask, count = re.subn(r'^  sha256 "[a-f0-9]{64}"$', f'  sha256 "{assets[0]["digest"][7:]}"', cask, flags=re.M)
    else:
        replacement = f'  sha256 arm:   "{assets[0]["digest"][7:]}",\n         intel: "{assets[1]["digest"][7:]}"'
        cask, count = re.subn(r'^  sha256 arm:   "[a-f0-9]{64}",\n         intel: "[a-f0-9]{64}"$', replacement, cask, flags=re.M)
    if count != 1:
        raise ValueError("Unexpected checksum stanza")
    result.update(assets=assets, cask=cask)
    return result


def publish(candidate, read=api):
    token = candidate["token"]
    if artifact.tag_commit(f"pwrdrvr/{APPS[token]}", f"v{candidate['version']}", read) != candidate["release_commit"]:
        raise ValueError("Release tag changed during validation")
    release = read(f"repos/pwrdrvr/{APPS[token]}/releases/latest")
    if (release["draft"] or release["prerelease"] or release["tag_name"] != f"v{candidate['version']}"
            or assets_for(token, release) != candidate["assets"]):
        raise ValueError("Stable Latest or assets changed during validation")
    endpoint = f"repos/pwrdrvr/homebrew-tap/contents/Casks/{token}.rb"
    current = read(f"{endpoint}?ref=main")
    cask = candidate["cask"]
    if base64.b64decode(current["content"]).decode() == cask:
        return "Already published"
    if current["sha"] != candidate["baseSha"]:
        raise ValueError("Published cask changed during validation")
    result = read(endpoint, {"message": f"{token} {candidate['version']}: publish validated Stable Latest",
                            "content": base64.b64encode(cask.encode()).decode(),
                            "sha": current["sha"], "branch": "main"})
    if base64.b64decode(read(f"{endpoint}?ref=main")["content"]).decode() != cask:
        raise ValueError("Cannot verify default-branch publication")
    return result["commit"]["html_url"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "publish"])
    parser.add_argument("token", choices=APPS)
    parser.add_argument("directory")
    args = parser.parse_args()
    directory = Path(args.directory)
    if args.operation == "plan":
        release = api(f"repos/pwrdrvr/{APPS[args.token]}/releases/latest")
        candidate = plan(args.token, Path(f"Casks/{args.token}.rb").read_text(), release, os.environ.get("REQUESTED_VERSION", ""))
        if candidate["changed"]:
            repo = f"pwrdrvr/{APPS[args.token]}"
            candidate["release_commit"] = artifact.tag_commit(repo, release["tag_name"])
            config = api(f"repos/{repo}/contents/apps/desktop/electron-builder.yml?ref={candidate['release_commit']}")
            set_macos(candidate, base64.b64decode(config["content"]).decode())
        (directory / "Casks").mkdir(parents=True, exist_ok=True)
        (directory / f"Casks/{args.token}.rb").write_text(candidate["cask"])
        (directory / "sync.json").write_text(json.dumps(candidate))
        (directory / "release.json").write_text(json.dumps(release))
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                output.write(f"changed={str(candidate['changed']).lower()}\nversion={candidate['version']}\nprevious={candidate['previous']}\n")
                for asset in candidate["assets"]:
                    arch = re.search(r"-(arm64|universal)\.dmg$", asset["name"])[1]
                    output.write(f"{arch}_url={asset['browser_download_url']}\n{arch}_sha256={asset['digest'][7:]}\n{arch}_size={asset['size']}\n")
        report = f"{args.token}: {candidate['previous']} -> {candidate['version']}; changed={candidate['changed']}"
    else:
        candidate = json.loads((directory / "sync.json").read_text())
        if candidate["token"] != args.token or (directory / f"Casks/{args.token}.rb").read_text() != candidate["cask"]:
            raise ValueError("Candidate artifact does not match its publication plan")
        report = f"Published {args.token} {candidate['version']}: {publish(candidate)}"
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(report + "\n")


if __name__ == "__main__":
    main()
