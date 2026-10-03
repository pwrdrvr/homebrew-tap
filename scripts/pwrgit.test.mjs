import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { prepareCask, assetsFor, resolveCask } from "./bump-pwrgit.mjs";
import { publish } from "./publish-pwrgit.mjs";

const current = `cask "pwrgit" do\n  version "0.27.0"\n  sha256 arm:   "${"a".repeat(64)}",\n         intel: "${"b".repeat(64)}"\nend\n`;
const payload = Buffer.from("signed artifact fixture");
function release(version = "0.29.0") {
  const tag_name = `v${version}`;
  return { tag_name, draft: false, prerelease: false, assets: ["arm64", "universal"].map((arch) => {
    const name = `PwrGit-${version}-${arch}.dmg`;
    return { name, browser_download_url: `https://github.com/pwrdrvr/PwrGit/releases/download/${tag_name}/${name}`, size: payload.length,
      digest: `sha256:${createHash("sha256").update(payload).digest("hex")}`, download_count: 5 };
  }) };
}
const fetchAsset = async () => new Response(payload);
test("accepts only promoted, signed versioned artifacts and rejects downgrades", async () => {
  await assert.rejects(prepareCask(current, { ...release(), prerelease: true }), /promoted/);
  await assert.rejects(prepareCask(current, release("0.26.0")), /downgrade/);
  const invalid = release();
  invalid.assets[0].browser_download_url = "https://example.com/alias.dmg";
  await assert.rejects(prepareCask(current, invalid), /Invalid versioned/);
  await assert.rejects(prepareCask(current, release(), async () => new Response("wrong bytes")), /digest\/size mismatch/);
});
test("downloads both architectures and skips unchanged versions", async () => {
  const calls = [];
  const plan = await prepareCask(current, release(), async (url) => { calls.push(url); return fetchAsset(); });
  assert.equal(calls.length, 2);
  assert.equal(plan.changed, true);
  assert.match(plan.cask, /version "0.29.0"/);
  const unchanged = await prepareCask(plan.cask, release(), async () => { throw new Error("must not download"); });
  assert.equal(unchanged.changed, false);
});
test("planning performs no downloads and replaced same-version bytes require validation", async () => {
  assert.equal(resolveCask(current, release()).changed, true);
  const plan = await prepareCask(current, release(), fetchAsset);
  assert.equal(resolveCask(plan.cask, release()).changed, false);
  const replaced = release();
  replaced.assets[0].digest = `sha256:${"f".repeat(64)}`;
  assert.equal(resolveCask(plan.cask, replaced).changed, true);
  await assert.rejects(prepareCask(plan.cask, replaced, fetchAsset), /digest\/size mismatch/);
});
test("publishes only the validated cask with a compare-and-swap and reads it back", async () => {
  const plan = await prepareCask(current, release(), fetchAsset);
  let content = current;
  let writes = 0;
  const api = (endpoint, ...args) => {
    if (endpoint.includes("releases/latest")) {
      const latest = release();
      latest.assets[0].download_count++; // Mutable counters do not invalidate artifact identity.
      return latest;
    }
    if (args.length) {
      assert.equal(args[1], "PUT");
      assert.ok(args.includes(`sha=${plan.baseSha}`));
      assert.ok(args.includes("branch=main"));
      content = plan.cask;
      writes++;
      return { commit: { html_url: "https://github.com/pwrdrvr/homebrew-tap/commit/fixture" } };
    }
    return { sha: plan.baseSha, content: Buffer.from(content).toString("base64") };
  };
  assert.match((await publish(plan, plan.cask, api)).commit, /commit\/fixture/);
  assert.deepEqual(await publish(plan, plan.cask, api), { alreadyCurrent: true });
  assert.equal(writes, 1);
});
test("refuses stale targets, changed artifacts or concurrently edited casks before writing", async () => {
  const plan = await prepareCask(current, release(), fetchAsset);
  for (const scenario of ["new release", "asset replaced", "cask edited"]) {
    const api = (endpoint, ...args) => {
      assert.equal(args.length, 0, "must not write an unvalidated candidate");
      if (endpoint.includes("releases/latest")) {
        const latest = release(scenario === "new release" ? "0.30.0" : "0.29.0");
        if (scenario === "asset replaced") latest.assets[0].digest = `sha256:${"f".repeat(64)}`;
        return latest;
      }
      return { sha: "concurrent-edit", content: Buffer.from(current).toString("base64") };
    };
    await assert.rejects(publish(plan, plan.cask, api), /changed during validation/);
  }
  assert.equal(assetsFor(release())[0].download_count, undefined);
});
