"""A cached validation skips work only for the exact still-open candidate."""

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bump_pwrsnap", ROOT / "scripts/bump-pwrsnap.py")
bump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump)


class PwrSnapDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.current = 'cask "pwrsnap" do\n  version "1.1.2"\n  sha256 "' + 'a' * 64 + '"\n  app "PwrSnap.app"\nend\n'
        self.release = dict(tag_name="v1.1.14", draft=False, prerelease=False, assets=[dict(
            name="PwrSnap-1.1.14-universal.dmg", id=123, updated_at="2026-10-03T00:00:00Z", size=1234,
            digest="sha256:" + "b" * 64, download_count=42,
            browser_download_url="https://github.com/pwrdrvr/PwrSnap/releases/download/v1.1.14/PwrSnap-1.1.14-universal.dmg",
        )])
        self.plan = bump.candidate(self.current, self.release)
        self.key = bump.validation_key(self.plan, "validator-1")
        self.pr = dict(state="open", base=dict(ref="main"), head=dict(ref="bump/pwrsnap-1.1.14", sha="candidate-head",
                       repo=dict(full_name="pwrdrvr/homebrew-tap")))

    def test_published_version_is_noop_even_with_changed_or_missing_asset_metadata(self):
        self.assertFalse(bump.candidate(self.plan["cask"], self.release)["changed"])
        release = copy.deepcopy(self.release)
        release["assets"][0]["digest"] = "sha256:" + "c" * 64
        self.assertFalse(bump.candidate(self.plan["cask"], release)["changed"])
        # Only the version tag is needed once it has been published.
        self.assertFalse(bump.candidate(self.plan["cask"], dict(tag_name="v1.1.14"))["changed"])

    def test_pending_candidate_requires_both_exact_cask_and_validation_record(self):
        pending = bump.pending_matches(self.plan, [self.pr], lambda sha: self.plan["cask"], lambda pr: ["Casks/pwrsnap.rb"])
        self.assertTrue(pending)
        plan = {**self.plan, "key": self.key, "pending": pending}
        self.assertTrue(bump.skip_validation(plan, self.key))
        self.assertFalse(bump.skip_validation(plan, ""))
        self.assertFalse(bump.skip_validation(plan, "different-validator-key"))
        self.assertFalse(bump.skip_validation({**plan, "pending": False}, self.key))

    def test_closed_fork_wrong_base_or_edited_pr_cannot_skip(self):
        for mutate in [lambda pr: pr.update(state="closed"), lambda pr: pr["head"]["repo"].update(full_name="fork/tap"),
                       lambda pr: pr["base"].update(ref="other"), lambda pr: pr["head"].update(ref="other")]:
            pr = copy.deepcopy(self.pr)
            mutate(pr)
            self.assertFalse(bump.pending_matches(self.plan, [pr], lambda sha: self.plan["cask"], lambda pr: ["Casks/pwrsnap.rb"]))
        self.assertFalse(bump.pending_matches(self.plan, [self.pr], lambda sha: self.current, lambda pr: ["Casks/pwrsnap.rb"]))
        self.assertFalse(bump.pending_matches(self.plan, [self.pr], lambda sha: self.plan["cask"], lambda pr: ["Casks/pwrsnap.rb", ".github/workflows/ci.yml"]))

    def test_release_identity_cask_and_validator_changes_invalidate_record(self):
        for field, value in [("id", 999), ("updated_at", "changed"), ("size", 5678), ("digest", "sha256:" + "c" * 64)]:
            release = copy.deepcopy(self.release)
            release["assets"][0][field] = value
            self.assertNotEqual(bump.validation_key(bump.candidate(self.current, release), "validator-1"), self.key)
        changed_cask = self.current.replace('app "PwrSnap.app"', 'app "Renamed.app"')
        self.assertNotEqual(bump.validation_key(bump.candidate(changed_cask, self.release), "validator-1"), self.key)
        self.assertNotEqual(bump.validation_key(self.plan, "validator-2"), self.key)
        release = copy.deepcopy(self.release)
        release["assets"][0]["download_count"] += 1000
        self.assertEqual(bump.validation_key(bump.candidate(self.current, release), "validator-1"), self.key)

    def test_latest_maintenance_hold_numeric_order_and_explicit_rollback(self):
        newer = self.current.replace('version "1.1.2"', 'version "1.2.0"')
        self.assertFalse(bump.candidate(newer, self.release)["changed"])
        self.assertTrue(bump.candidate(newer, self.release, "1.1.14")["changed"])
        self.assertTrue(bump.candidate(self.current.replace("1.1.2", "1.1.9"), self.release)["changed"])
        for value in ["1.1.14\nevil=1", "1.1.14-alpha", ""]:
            with self.assertRaises(ValueError):
                bump.version(value)

    def test_missing_digest_and_prerelease_fail_without_downloading(self):
        release = copy.deepcopy(self.release)
        del release["assets"][0]["digest"]
        with self.assertRaises(ValueError):
            bump.candidate(self.current, release)
        with self.assertRaises(ValueError):
            bump.candidate(self.current, {**self.release, "prerelease": True})
