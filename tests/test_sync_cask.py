"""Stable-only publication, immutable metadata, stale target and concurrent edits."""
import base64
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync", ROOT / "scripts/sync-cask.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncCaskTests(unittest.TestCase):
    def release(self, token):
        app = sync.APPS[token]
        arches = ["universal"] if token == "pwrsnap" else ["arm64", "universal"]
        return dict(tag_name="v9.0.0", draft=False, prerelease=False, assets=[
            dict(name=f"{app}-9.0.0-{arch}.dmg", id=i, size=10,
                 digest="sha256:" + str(i + 1) * 64,
                 browser_download_url=f"https://github.com/pwrdrvr/{app}/releases/download/v9.0.0/{app}-9.0.0-{arch}.dmg")
            for i, arch in enumerate(arches)])

    def test_all_three_apps_preserve_cask_and_pin_correct_architecture_hashes(self):
        for token in sync.APPS:
            with self.subTest(token=token):
                current = (ROOT / f"Casks/{token}.rb").read_text()
                candidate = sync.plan(token, current, self.release(token))
                self.assertTrue(candidate["changed"])
                self.assertEqual(sync.version(candidate["cask"]), "9.0.0")
                self.assertIn("auto_updates true", candidate["cask"])
                self.assertEqual(len(candidate["assets"]), 1 if token == "pwrsnap" else 2)
                for asset in candidate["assets"]:
                    self.assertIn(asset["digest"][7:], candidate["cask"])

    def test_published_version_skips_asset_inspection(self):
        current = (ROOT / "Casks/pwrsnap.rb").read_text()
        release = dict(tag_name="v" + sync.version(current), draft=False, prerelease=False)
        self.assertFalse(sync.plan("pwrsnap", current, release)["changed"])

    def test_prerelease_stale_dispatch_bad_assets_and_downgrade_are_rejected(self):
        current = (ROOT / "Casks/pwrsnap.rb").read_text()
        release = self.release("pwrsnap")
        for change in [dict(prerelease=True), dict(draft=True), dict(tag_name="v9.0.0-beta"), dict(tag_name="v0.0.1")]:
            with self.assertRaises(ValueError):
                sync.plan("pwrsnap", current, {**release, **change})
        with self.assertRaisesRegex(ValueError, "no longer Stable Latest"):
            sync.plan("pwrsnap", current, release, "8.0.0")
        release["assets"][0]["digest"] = None
        with self.assertRaises(ValueError):
            sync.plan("pwrsnap", current, release)

    def test_publication_rechecks_assets_and_uses_cask_compare_and_swap(self):
        current = (ROOT / "Casks/pwrsnap.rb").read_text()
        release = self.release("pwrsnap")
        candidate = sync.plan("pwrsnap", current, release)
        candidate["release_commit"] = "a" * 40
        state = dict(content=base64.b64encode(current.encode()).decode(), sha=candidate["baseSha"])
        writes = []
        def read(endpoint, payload=None):
            if "/git/ref/" in endpoint:
                return dict(object=dict(type="commit", sha="a" * 40))
            if payload:
                writes.append(payload)
                state["content"] = payload["content"]
                return dict(commit=dict(html_url="https://github.com/pwrdrvr/homebrew-tap/commit/example"))
            return release if "/releases/" in endpoint else state
        original = copy.deepcopy(release)
        release["assets"][0]["size"] += 1
        with self.assertRaisesRegex(ValueError, "assets changed"):
            sync.publish(candidate, read)
        release.update(original)
        state["sha"] = "changed"
        with self.assertRaisesRegex(ValueError, "cask changed"):
            sync.publish(candidate, read)
        self.assertEqual(writes, [])
        state["sha"] = candidate["baseSha"]
        self.assertIn("commit/example", sync.publish(candidate, read))
        self.assertEqual(writes[0]["branch"], "main")
        self.assertEqual(sync.publish(candidate, read), "Already published")

    def test_release_macos_floor_updates_cask_and_rejects_unknown_mapping(self):
        candidate = sync.plan("pwragent", (ROOT / "Casks/pwragent.rb").read_text(), self.release("pwragent"))
        sync.set_macos(candidate, '    LSMinimumSystemVersion: "13.0"\n')
        self.assertIn("depends_on macos: :ventura", candidate["cask"])
        self.assertEqual(candidate["minimum_os"], "13.0")
        with self.assertRaises(ValueError):
            sync.set_macos(candidate, '    LSMinimumSystemVersion: "99.0"\n')
