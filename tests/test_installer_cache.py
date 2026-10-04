"""Exercise byte identity, corruption rejection and Homebrew cache seeding."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer_cache", ROOT / "scripts/installer-cache.py")
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)


class InstallerCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = b"signed installer fixture"
        self.sha = hashlib.sha256(self.payload).hexdigest()
        self.url = "https://github.com/pwrdrvr/PwrGit/releases/download/v0.29.0/PwrGit-0.29.0-arm64.dmg"
        self.plan = cache.asset_plan(self.url, self.sha, "0.29.0", "arm64", len(self.payload))
        self.plan["path"] = str(self.root / "installer.dmg")

    def test_exact_bytes_download_once_and_restore_without_network(self):
        calls = []
        def download(args, check):
            calls.append(args[-1])
            Path(args[args.index("-o") + 1]).write_bytes(self.payload)
        self.assertEqual(cache.ensure(self.plan, download), "downloaded")
        self.assertEqual(cache.ensure(self.plan, download), "restored")
        self.assertEqual(calls, [self.url])

    def test_corrupt_restored_bytes_and_wrong_size_are_rejected(self):
        path = Path(self.plan["path"])
        for content, size in [(b"bad cache", len(self.payload)), (self.payload, len(self.payload) + 1)]:
            with self.subTest(content=content):
                path.write_bytes(content)
                with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
                    cache.ensure({**self.plan, "size": size}, lambda *a, **k: self.fail("must not trust corrupt cache"))

    def test_failed_download_is_not_promoted_to_cache(self):
        def download(args, check):
            Path(args[args.index("-o") + 1]).write_bytes(b"wrong bytes")
        with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
            cache.ensure(self.plan, download)
        self.assertFalse(Path(self.plan["path"]).exists())
        self.assertFalse(Path(self.plan["path"]).with_suffix(".partial").exists())

    def test_key_separates_version_architecture_checksum_and_url(self):
        cases = [
            cache.asset_plan(self.url, "f" * 64, "0.29.0", "arm64"),
            cache.asset_plan(self.url.replace("arm64", "universal"), self.sha, "0.29.0", "universal"),
            cache.asset_plan(self.url.replace("0.29.0", "0.30.0"), self.sha, "0.30.0", "arm64"),
            cache.asset_plan(self.url.replace("PwrGit", "PwrAgent"), self.sha, "0.29.0", "arm64"),
        ]
        self.assertEqual(len({self.plan["key"], *(plan["key"] for plan in cases)}), 5)
        with self.assertRaises(ValueError):
            cache.asset_plan(self.url, self.sha, "0.29.0", "universal")

    def test_homebrew_native_metadata_must_match_release_and_seeds_actual_path(self):
        target = self.root / "Homebrew/downloads/url-hash--PwrGit.dmg"
        def api(*args):
            if args[0] == "gh":
                return json.dumps({"assets": [dict(name="PwrGit-0.29.0-arm64.dmg", browser_download_url=self.url,
                                                    digest=f"sha256:{self.sha}", size=len(self.payload))]})
            if args[1] == "info":
                return json.dumps({"casks": [dict(url=self.url, sha256=self.sha, version="0.29.0")]})
            self.assertEqual(args, ("brew", "--cache", "--cask", "pwrdrvr/tap/pwrgit"))
            return str(target)
        plan = cache.brew_plan("pwrdrvr/tap/pwrgit", api)
        plan["path"] = self.plan["path"]
        Path(plan["path"]).write_bytes(self.payload)
        cache.seed_brew(plan, api)
        self.assertEqual(target.read_bytes(), self.payload)
        def mismatched_api(*args):
            value = api(*args)
            return value.replace(self.sha, "f" * 64) if args[0] == "gh" else value
        with self.assertRaisesRegex(ValueError, "differs from the live release"):
            cache.brew_plan("pwrdrvr/tap/pwrgit", mismatched_api)
