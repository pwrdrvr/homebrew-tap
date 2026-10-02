#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";

const gh = (path) => JSON.parse(execFileSync("gh", ["api", path], { encoding: "utf8" }));
const release = gh("repos/pwrdrvr/PwrGit/releases/latest");
if (release.draft || release.prerelease || !/^v\d+\.\d+\.\d+$/.test(release.tag_name)) {
  throw new Error("PwrGit Latest must be a promoted suffix-free stable release");
}
const version = release.tag_name.slice(1);
const path = "Casks/pwrgit.rb";
const current = readFileSync(path, "utf8");
const previous = current.match(/^  version "(\d+\.\d+\.\d+)"$/m)?.[1];
if (!previous) throw new Error("Cannot read current cask version");
const compare = (a, b) => {
  for (let i = 0; i < 3; i++) {
    const delta = Number(a.split(".")[i]) - Number(b.split(".")[i]);
    if (delta) return delta;
  }
  return 0;
};
if (compare(previous, version) > 0) throw new Error("Refusing to downgrade the PwrGit cask");
if (compare(previous, version) === 0) {
  console.log(`PwrGit ${version} is current`);
  process.exit(0);
}
const hashes = [];
for (const arch of ["arm64", "universal"]) {
  const name = `PwrGit-${version}-${arch}.dmg`;
  const assets = release.assets.filter((a) => a.name === name);
  const url = `https://github.com/pwrdrvr/PwrGit/releases/download/${release.tag_name}/${name}`;
  if (assets.length !== 1 || assets[0].browser_download_url !== url || !/^sha256:[a-f0-9]{64}$/.test(assets[0].digest ?? "")) {
    throw new Error(`Invalid versioned release asset ${name}`);
  }
  const response = await fetch(url);
  if (!response.ok || !response.body) throw new Error(`Download failed: ${name}`);
  const hash = createHash("sha256");
  let size = 0;
  for await (const chunk of response.body) { hash.update(chunk); size += chunk.length; }
  const sha = hash.digest("hex");
  if (`sha256:${sha}` !== assets[0].digest || size !== assets[0].size) throw new Error(`Release digest/size mismatch: ${name}`);
  hashes.push(sha);
}
if (!/^  sha256 arm:   "[a-f0-9]{64}",\n         intel: "[a-f0-9]{64}"$/m.test(current)) throw new Error("Unexpected architecture checksum stanzas");
writeFileSync(path, current.replace(/^  version ".*"$/m, `  version "${version}"`)
  .replace(/^  sha256 arm:   ".*",\n         intel: ".*"$/m, `  sha256 arm:   "${hashes[0]}",\n         intel: "${hashes[1]}"`));
console.log(`PwrGit ${previous} -> ${version}; both downloads verified`);
