#!/usr/bin/env node
import { appendFileSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { assetsFor, caskVersion, gh, stableVersion } from "./bump-pwrgit.mjs";

export async function publish(plan, cask, api = gh) {
  if (caskVersion(cask) !== plan.version) throw new Error("Candidate cask version does not match validation");
  const release = await api("repos/pwrdrvr/PwrGit/releases/latest");
  if (stableVersion(release) !== plan.version || JSON.stringify(assetsFor(release)) !== JSON.stringify(plan.assets)) {
    throw new Error("Stable Latest or release assets changed during validation; rerun synchronization");
  }
  const endpoint = "repos/pwrdrvr/homebrew-tap/contents/Casks/pwrgit.rb";
  const current = await api(`${endpoint}?ref=main`);
  if (Buffer.from(current.content, "base64").toString("utf8") === cask) return { alreadyCurrent: true };
  if (current.sha !== plan.baseSha) throw new Error("Published cask changed during validation; rerun synchronization");
  const result = await api(endpoint, "--method", "PUT", "-f", `message=pwrgit ${plan.version}: publish validated Stable Latest`,
    "-f", `content=${Buffer.from(cask).toString("base64")}`, "-f", `sha=${current.sha}`, "-f", "branch=main");
  const published = await api(`${endpoint}?ref=main`);
  if (Buffer.from(published.content, "base64").toString("utf8") !== cask) throw new Error("Default-branch publication could not be verified");
  return { commit: result.commit.html_url };
}
async function run() {
  const directory = process.argv[2] ?? "distribution";
  const plan = JSON.parse(readFileSync(join(directory, "sync.json"), "utf8"));
  const result = await publish(plan, readFileSync(join(directory, "Casks/pwrgit.rb"), "utf8"));
  const summary = `Published PwrGit ${plan.version} to Homebrew tap main. ${result.commit ?? "Already current."}\nSource: https://github.com/pwrdrvr/homebrew-tap/blob/main/Casks/pwrgit.rb\n`;
  console.log(summary);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, summary);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) run().catch((error) => { console.error(error.message); process.exitCode = 1; });
