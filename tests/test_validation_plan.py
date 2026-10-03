"""All three apps share a guard bound to cask/release/code/native coverage."""

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validation_plan", ROOT / "scripts/validation-plan.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


class ValidationGuardTests(unittest.TestCase):
    def setUp(self):
        self.tokens = ["pwragent", "pwrgit", "pwrsnap"]
        self.casks = {token: f'cask "{token}" do\n  version "1.2.3"\nend\n' for token in self.tokens}
        self.release = dict(tag_name="v1.2.3", assets=[dict(name="App-1.2.3-universal.dmg", id=42,
                            updated_at="2026-10-03", digest="sha256:" + "a" * 64, size=123,
                            browser_download_url="https://github.com/pwrdrvr/App/releases/download/v1.2.3/App-1.2.3-universal.dmg",
                            download_count=100)])
        self.caches = []
        self.refs = {"refs/heads/main", "refs/pull/10/merge"}

    def matrix(self, code="validator-1", release=None):
        return validation.make_matrix(self.tokens, self.casks.get, lambda *args: release or self.release,
                                      code, lambda key: self.caches, self.refs)

    def warm(self):
        matrix, _ = self.matrix()
        self.caches = [{"key": row["key"], "ref": "refs/heads/main"} for row in matrix["include"]]

    def test_all_apps_cold_then_no_native_jobs_for_identical_candidates(self):
        matrix, reused = self.matrix()
        self.assertEqual(len(matrix["include"]), 6)
        self.assertEqual(reused, [])
        self.warm()
        matrix, reused = self.matrix()
        self.assertEqual(matrix["include"], [])
        self.assertEqual(len(reused), 6)

    def test_only_changed_cask_revalidates_both_native_architectures(self):
        self.warm()
        for token in self.tokens:
            original = self.casks[token]
            self.casks[token] += "# revised cask\n"
            matrix, reused = self.matrix()
            self.assertEqual([row["cask"] for row in matrix["include"]], [token, token])
            self.assertEqual({row["os"] for row in matrix["include"]}, {"macos-26", "macos-15-intel"})
            self.assertEqual(len(reused), 4)
            self.casks[token] = original

    def test_release_replacement_or_shared_validator_change_revalidates(self):
        self.warm()
        for field, value in [("digest", "sha256:" + "b" * 64), ("id", 99), ("updated_at", "changed"), ("size", 456)]:
            release = copy.deepcopy(self.release)
            release["assets"][0][field] = value
            self.assertEqual(len(self.matrix(release=release)[0]["include"]), 6)
        self.assertEqual(len(self.matrix(code="validator-2")[0]["include"]), 6)
        release = copy.deepcopy(self.release)
        release["assets"][0]["download_count"] += 1000
        self.assertEqual(self.matrix(release=release)[0]["include"], [])

    def test_pr_records_cannot_skip_main_or_sibling_validation(self):
        self.warm()
        for record in self.caches:
            record["ref"] = "refs/pull/10/merge"
        self.assertEqual(self.matrix()[0]["include"], [])
        for refs in [{"refs/heads/main"}, {"refs/heads/main", "refs/pull/11/merge"}]:
            self.refs = refs
            self.assertEqual(len(self.matrix()[0]["include"]), 6)

    def test_cache_api_prefix_match_and_other_runner_cannot_skip(self):
        self.warm()
        key = self.caches[0]["key"]
        self.assertFalse(validation.known_success(key, [dict(key=key + "-different", ref="refs/heads/main")], self.refs))
        assets = validation.release_identity(self.casks["pwrgit"], self.release)
        arm = validation.validation_key("pwrgit", self.casks["pwrgit"], assets, "code", "macos-26", "arm64")
        intel = validation.validation_key("pwrgit", self.casks["pwrgit"], assets, "code", "macos-15-intel", "x86_64")
        future = validation.validation_key("pwrgit", self.casks["pwrgit"], assets, "code", "macos-27", "arm64")
        self.assertEqual(len({arm, intel, future}), 3)

    def test_docs_only_selection_never_queries_releases_or_caches(self):
        def forbidden(*args):
            self.fail("Docs-only selection must not query release/cache APIs")
        self.assertEqual(validation.make_matrix([], forbidden, forbidden, "code", forbidden, self.refs), ({"include": []}, []))
