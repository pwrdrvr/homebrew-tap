"""All three apps share a guard bound to cask/release/code/native coverage."""

import copy
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_pwrsnap_cli_warms_one_universal_installer_for_both_native_jobs(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            (root / "Casks").mkdir()
            sha = "a" * 64
            url = "https://github.com/pwrdrvr/PwrSnap/releases/download/v1.2.3/PwrSnap-1.2.3-universal.dmg"
            cask = self.casks["pwrsnap"] + f'  sha256 "{sha}"\n  url "{url.replace("1.2.3", "#{version}")}"\n'
            (root / "Casks/pwrsnap.rb").write_text(cask)
            (root / "selection.json").write_text(json.dumps(dict(casks=["pwrsnap"])))
            release = copy.deepcopy(self.release)
            release["assets"][0].update(name="PwrSnap-1.2.3-universal.dmg", browser_download_url=url)
            api_calls = []
            def command(*args):
                api_calls.append(args)
                return "" if "actions/caches?" in " ".join(args) else json.dumps(release)
            original = Path.cwd()
            try:
                os.chdir(root)
                with patch.object(validation, "command", side_effect=command), patch.object(validation, "validation_code", return_value="code"), \
                        patch("sys.argv", ["validation-plan.py", "--selection", "selection.json"]), \
                        patch.dict(os.environ, {"GITHUB_OUTPUT": str(root / "output")}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                    validation.main()
                output = dict(line.split("=", 1) for line in (root / "output").read_text().splitlines())
                self.assertEqual({row["os"] for row in json.loads(output["matrix"])["include"]},
                                 {"macos-26", "macos-15-intel"})
                self.assertEqual(json.loads(output["pwrsnap_installer"]),
                                 dict(url=url, sha256=sha, size=123, version="1.2.3", architecture="universal"))
                self.assertEqual(sum("releases/tags/" in args[2] for args in api_calls), 1)
                # Fully reused validations must not touch installers, nor should
                # a docs-only/PwrGit-only selection prefetch a PwrSnap release.
                forbidden = lambda *args: self.fail("no required PwrSnap validation")
                for matrix in [{"include": []}, {"include": [{"cask": "pwrgit"}]}]:
                    self.assertEqual(validation.shared_pwrsnap_installer(matrix, forbidden, forbidden), {})
                with self.assertRaisesRegex(ValueError, "checksum differs"):
                    bad = copy.deepcopy(release)
                    bad["assets"][0]["digest"] = "sha256:" + "b" * 64
                    validation.shared_pwrsnap_installer(json.loads(output["matrix"]), lambda _: cask, lambda *_: bad)
                changed = cask.replace("PwrSnap-#{version}-universal.dmg", "custom-universal.dmg")
                self.assertEqual(validation.shared_pwrsnap_installer(json.loads(output["matrix"]), lambda _: changed, forbidden), {})
            finally:
                os.chdir(original)

    def test_sync_cli_plans_candidate_and_separates_upgrade_coverage(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            (root / "Casks").mkdir()
            (root / "distribution/Casks").mkdir(parents=True)
            cask = self.casks["pwrgit"] + 'url "https://github.com/pwrdrvr/PwrGit/releases/download/v#{version}/App-#{version}-universal.dmg"\n'
            (root / "Casks/pwrgit.rb").write_text(cask)
            (root / "distribution/Casks/pwrgit.rb").write_text(cask)
            (root / "distribution/release.json").write_text(json.dumps(self.release))
            def command(*args):
                self.assertEqual(args[:2], ("gh", "api"))
                if "actions/caches?" in " ".join(args):
                    return ""
                self.assertIn("releases/tags/v1.2.3", args[2])
                return json.dumps(self.release)
            original = Path.cwd()
            try:
                os.chdir(root)
                with patch.object(validation, "command", side_effect=command), patch.object(validation, "validation_code", return_value="code"), \
                        patch("sys.argv", ["validation-plan.py", "--pwrgit-sync", "distribution"]), \
                        patch.dict(os.environ, {"GITHUB_OUTPUT": str(root / "output")}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                    validation.main()
                matrix = json.loads((root / "output").read_text().removeprefix("matrix="))
                self.assertEqual(len(matrix["include"]), 2)
                self.assertTrue(all(row["key"].startswith("tap-sync-validation-v1-pwrgit-") for row in matrix["include"]))
            finally:
                os.chdir(original)

    def test_force_validation_ignores_success_records(self):
        self.warm()
        matrix, reused = validation.make_matrix(self.tokens, self.casks.get, lambda *args: self.release,
                                               "validator-1", lambda key: self.caches, self.refs, force=True)
        self.assertEqual(len(matrix["include"]), 6)
        self.assertEqual(reused, [])
