#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createReadStream } from "node:fs";
import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

export const gh = (path, ...args) => JSON.parse(execFileSync("gh", ["api", path, ...args], { encoding: "utf8" }));
export function caskVersion(text) {
  const version = text.match(/^  version "(\d+\.\d+\.\d+)"$/m)?.[1];
  if (!version) throw new Error("Cannot read current cask version");
  return version;
}
export function stableVersion(release) {
  if (release.draft || release.prerelease || !/^v\d+\.\d+\.\d+$/.test(release.tag_name)) {
    throw new Error("PwrGit Latest must be a promoted suffix-free stable release");
  }
  return release.tag_name.slice(1);
}
export function compare(a, b) {
  for (let i = 0; i < 3; i++) {
    const delta = Number(a.split(".")[i]) - Number(b.split(".")[i]);
    if (delta) return Math.sign(delta);
  }
  return 0;
}
export function assetsFor(release) {
  const version = stableVersion(release);
  return ["arm64", "universal"].map((arch) => {
    const name = `PwrGit-${version}-${arch}.dmg`;
    const matches = release.assets.filter((a) => a.name === name);
    const url = `https://github.com/pwrdrvr/PwrGit/releases/download/${release.tag_name}/${name}`;
    if (matches.length !== 1 || matches[0].browser_download_url !== url || !/^sha256:[a-f0-9]{64}$/.test(matches[0].digest ?? "") || matches[0].size <= 0) {
      throw new Error(`Invalid versioned release asset ${name}`);
    }
    const { browser_download_url, digest, size } = matches[0];
    return { name, browser_download_url, digest, size };
  });
}
export function resolveCask(current, release) {
  const version = stableVersion(release);
  const previous = caskVersion(current);
  if (compare(previous, version) > 0) throw new Error("Refusing to downgrade the PwrGit cask");
  const assets = assetsFor(release);
  const baseSha = createHash("sha1").update(`blob ${Buffer.byteLength(current)}\0`).update(current).digest("hex");
  const checksums = current.match(/^  sha256 arm:   "([a-f0-9]{64})",\n         intel: "([a-f0-9]{64})"$/m);
  // A replaced release asset must not hide behind the same version's no-op.
  const sameBytes = checksums && assets.every((asset, index) => asset.digest === `sha256:${checksums[index + 1]}`);
  return { version, previous, baseSha, assets, changed: previous !== version || !sameBytes, cask: current };
}
export async function prepareCask(current, release, fetchAsset = fetch) {
  const plan = resolveCask(current, release);
  const { version, previous, baseSha, assets } = plan;
  if (!plan.changed) return plan;
  const hashes = [];
  for (const asset of assets) {
    const response = await fetchAsset(asset.browser_download_url);
    if (!response.ok || !response.body) throw new Error(`Download failed: ${asset.name}`);
    const hash = createHash("sha256");
    let size = 0;
    for await (const chunk of response.body) { hash.update(chunk); size += chunk.length; }
    const sha = hash.digest("hex");
    if (`sha256:${sha}` !== asset.digest || size !== asset.size) throw new Error(`Release digest/size mismatch: ${asset.name}`);
    hashes.push(sha);
  }
  if (!/^  sha256 arm:   "[a-f0-9]{64}",\n         intel: "[a-f0-9]{64}"$/m.test(current)) throw new Error("Unexpected architecture checksum stanzas");
  const cask = current.replace(/^  version ".*"$/m, `  version "${version}"`)
    .replace(/^  sha256 arm:   ".*",\n         intel: ".*"$/m, `  sha256 arm:   "${hashes[0]}",\n         intel: "${hashes[1]}"`);
  return { version, previous, baseSha, assets, changed: true, cask };
}
async function run() {
  const planning = process.argv[2] === "--plan";
  const directory = (planning ? process.argv[3] : process.argv[2]) ?? "distribution";
  const release = planning ? gh("repos/pwrdrvr/PwrGit/releases/latest") :
    JSON.parse(readFileSync(join(directory, "release.json"), "utf8"));
  if (process.env.REQUESTED_VERSION && process.env.REQUESTED_VERSION !== stableVersion(release)) {
    throw new Error("Requested version is no longer Stable Latest; refusing stale dispatch");
  }
  const current = readFileSync("Casks/pwrgit.rb", "utf8");
  const files = [process.env.ARM64_INSTALLER, process.env.UNIVERSAL_INSTALLER];
  const cachedAsset = async (url) => {
    const index = assetsFor(release).findIndex((asset) => asset.browser_download_url === url);
    if (!files[index]) throw new Error("Verified installer path required; run the cache steps first");
    return { ok: true, body: createReadStream(files[index]) };
  };
  const { cask, ...plan } = planning ? resolveCask(current, release) : await prepareCask(current, release, cachedAsset);
  mkdirSync(join(directory, "Casks"), { recursive: true });
  writeFileSync(join(directory, "Casks/pwrgit.rb"), cask);
  writeFileSync(join(directory, "sync.json"), `${JSON.stringify(plan, null, 2)}\n`);
  if (planning) writeFileSync(join(directory, "release.json"), `${JSON.stringify(release, null, 2)}\n`);
  if (process.env.GITHUB_OUTPUT) {
    appendFileSync(process.env.GITHUB_OUTPUT, `version=${plan.version}\nprevious=${plan.previous}\nchanged=${plan.changed}\n`);
    for (const [index, asset] of plan.assets.entries()) {
      const arch = index === 0 ? "arm64" : "universal";
      appendFileSync(process.env.GITHUB_OUTPUT, `${arch}_url=${asset.browser_download_url}\n${arch}_sha256=${asset.digest.slice(7)}\n${arch}_size=${asset.size}\n`);
    }
  }
  console.log(`PwrGit ${plan.previous} -> ${plan.version}; changed=${plan.changed}`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) run().catch((error) => { console.error(error.message); process.exitCode = 1; });
