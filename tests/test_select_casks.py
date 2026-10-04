"""Exercise selection against real Git histories, including PR/base divergence."""

import json
import os
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "scripts/select-casks.py"
WORKFLOW = ROOT / ".github/workflows/ci.yml"


class CaskSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "ci@example.test")
        self.git("config", "user.name", "CI Test")
        # Deliberately stale sibling: selection must not load or audit it.
        self.write("Casks/pwrsnap.rb", 'cask "pwrsnap" do\n  version "1.1.2"\nend\n')
        self.write("README.md", "Tap\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ).stdout.strip()

    def write(self, path, content="changed\n"):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "test change")

    def select(self, event="pull_request", base=None, check=True):
        command = ["python3", str(SELECTOR), "--event", event]
        if base is not None or event in {"pull_request", "push"}:
            command.extend(["--base", self.base if base is None else base])
        result = subprocess.run(
            command, cwd=self.repo, check=check, capture_output=True, text=True,
        )
        return json.loads(result.stdout)["casks"] if check else result

    def select_from_workflow(self, event="push", base=None):
        # Execute the actual workflow shell block so the regression also checks
        # that the fetch runs before the selector, rather than duplicating it.
        match = re.search(
            r"      - name: Select casks\n.*?        run: \|\n((?:          [^\n]*\n|\n)+)",
            WORKFLOW.read_text(), re.S,
        )
        self.assertIsNotNone(match)
        self.write("scripts/select-casks.py", SELECTOR.read_text())
        runner = Path(self.temp.name) / "runner"
        runner.mkdir(exist_ok=True)
        subprocess.run(
            ["bash", "-c", textwrap.dedent(match[1])], cwd=self.repo, check=True,
            capture_output=True, text=True,
            env={**os.environ, "EVENT": event, "BASE": self.base if base is None else base,
                 "RUNNER_TEMP": str(runner), "GITHUB_STEP_SUMMARY": str(runner / "summary")},
        )
        return json.loads((runner / "cask-selection.json").read_text())["casks"]

    def add_pwrgit(self):
        self.write("Casks/pwrgit.rb", 'cask "pwrgit" do\n  version "0.29.0"\nend\n')

    def both_in_base(self):
        self.add_pwrgit()
        self.commit()
        self.base = self.git("rev-parse", "HEAD")

    def test_registration_excludes_stale_sibling(self):
        self.add_pwrgit()
        self.write("scripts/bump-pwrgit.mjs")
        self.write(".github/workflows/bump-pwrgit.yml")
        self.write("README.md", "PwrGit registration\n")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit"])

    def test_existing_cask_update(self):
        self.both_in_base()
        self.write("Casks/pwrgit.rb")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit"])

    def test_multiple_cask_updates(self):
        self.both_in_base()
        self.write("Casks/pwrgit.rb")
        self.write("Casks/pwrsnap.rb")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit", "pwrsnap"])

    def test_future_registration_requires_no_matrix_edit(self):
        self.write("Casks/pwragent.rb")
        self.write("scripts/bump-pwragent.py")
        self.write(".github/workflows/bump-pwragent.yaml")
        self.commit()
        self.assertEqual(self.select(), ["pwragent"])

    def test_shared_changes_select_all(self):
        self.both_in_base()
        for path in [".github/workflows/ci.yml", "scripts/select-casks.py",
                     "tests/test_select_casks.py", "lib/shared.rb", ".github/actions/setup/action.yml"]:
            with self.subTest(path=path):
                self.write(path)
                self.commit()
                self.assertEqual(self.select(), ["pwrgit", "pwrsnap"])
                self.base = self.git("rev-parse", "HEAD")

    def test_registration_with_shared_ci_change_selects_all(self):
        self.add_pwrgit()
        self.write(".github/workflows/ci.yml")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit", "pwrsnap"])

    def test_app_specific_bump_changes(self):
        self.both_in_base()
        self.write("scripts/bump-pwrgit.mjs")
        self.write(".github/workflows/bump-pwrgit.yml")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit"])

    def test_legacy_pwrsnap_bump_changes(self):
        self.both_in_base()
        self.write("scripts/bump-cask.sh")
        self.write(".github/workflows/bump.yml")
        self.commit()
        self.assertEqual(self.select(), ["pwrsnap"])

    def test_unknown_bump_tooling_is_shared(self):
        self.both_in_base()
        self.write("scripts/bump-unknown.py")
        self.commit()
        self.assertEqual(self.select(), ["pwrgit", "pwrsnap"])

    def test_docs_only_selects_none(self):
        self.write("README.md")
        self.write("docs/example.txt")
        self.commit()
        self.assertEqual(self.select(), [])

    def test_deleted_cask_is_not_installed(self):
        self.both_in_base()
        (self.repo / "Casks/pwrgit.rb").unlink()
        self.commit()
        self.assertEqual(self.select(), [])

    def test_renamed_cask_uses_new_token(self):
        self.git("mv", "Casks/pwrsnap.rb", "Casks/pwragent.rb")
        self.commit()
        self.assertEqual(self.select(), ["pwragent"])

    def test_manual_runs_select_all(self):
        self.both_in_base()
        self.assertEqual(self.select("workflow_dispatch"), ["pwrgit", "pwrsnap"])

    def test_push_single_cask_and_docs_only(self):
        self.both_in_base()
        self.write("Casks/pwrgit.rb")
        self.commit()
        self.assertEqual(self.select("push"), ["pwrgit"])
        self.base = self.git("rev-parse", "HEAD")
        self.write("README.md")
        self.commit()
        self.assertEqual(self.select("push"), [])

    def test_multi_commit_push_and_shared_validation_change(self):
        self.both_in_base()
        self.write("Casks/pwrgit.rb")
        self.commit()
        self.write("README.md")
        self.commit()
        self.assertEqual(self.select("push"), ["pwrgit"])
        self.write(".github/actions/cache-installer/action.yml")
        self.commit()
        self.assertEqual(self.select("push"), ["pwrgit", "pwrsnap"])

    def test_push_force_update_uses_two_dot_diff(self):
        self.both_in_base()
        original = self.base
        self.write("Casks/pwrsnap.rb", "changed on replaced main\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD")
        self.git("checkout", "--detach", original)
        self.write("Casks/pwrgit.rb")
        self.commit()
        self.assertEqual(self.select("push"), ["pwrgit", "pwrsnap"])

    def test_force_push_fresh_clone_fetches_unreachable_before_commit(self):
        self.both_in_base()
        original = self.base
        self.git("checkout", "-B", "main")
        self.write("Casks/pwrsnap.rb", "changed on replaced main\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD")
        self.git("checkout", "--detach", original)
        self.write("Casks/pwrgit.rb")
        self.commit()
        replacement = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/heads/main", replacement, self.base)
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        # Like GitHub, retain replaced objects on the server for explicit SHA
        # fetches, without advertising them as a branch/tag to a fresh client.
        self.git("config", "uploadpack.allowAnySHA1InWant", "true")
        source = self.repo
        clone = source / "fresh-clone"
        self.git("clone", "--no-local", "--branch", "main", source.as_uri(), str(clone))
        self.repo = clone
        missing = subprocess.run(["git", "cat-file", "-e", f"{self.base}^{{commit}}"],
                                 cwd=clone, capture_output=True)
        self.assertNotEqual(missing.returncode, 0)
        # Prove the original failure, then run the workflow's recovery path.
        failure = self.select("push", check=False)
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("Invalid revision range", failure.stderr)
        self.assertEqual(self.select_from_workflow(), ["pwrgit", "pwrsnap"])
        self.assertEqual(self.git("rev-parse", "FETCH_HEAD"), self.base)
        self.assertEqual(self.git("rev-parse", "HEAD"), replacement)

    def test_workflow_existing_push_base_needs_no_remote_fetch(self):
        self.both_in_base()
        self.write("Casks/pwrgit.rb")
        self.commit()
        # This fixture has no origin; any needless fetch would fail.
        self.assertEqual(self.select_from_workflow(), ["pwrgit"])

    def test_workflow_manual_and_new_branch_need_no_remote_fetch(self):
        self.both_in_base()
        for event, base in [("workflow_dispatch", ""), ("push", "0" * 40), ("pull_request", self.base)]:
            with self.subTest(event=event):
                expected = [] if event == "pull_request" else ["pwrgit", "pwrsnap"]
                self.assertEqual(self.select_from_workflow(event, base), expected)

    def test_new_branch_push_selects_all(self):
        self.both_in_base()
        self.assertEqual(self.select("push", base="0" * 40), ["pwrgit", "pwrsnap"])

    def test_empty_tap(self):
        (self.repo / "Casks/pwrsnap.rb").unlink()
        self.commit()
        self.assertEqual(self.select("push"), [])

    def test_base_only_changes_do_not_select_siblings(self):
        self.git("checkout", "-qb", "base-update")
        self.write("Casks/pwrsnap.rb", 'version "1.1.14"\n')
        self.commit()
        newer_base = self.git("rev-parse", "HEAD")
        self.git("checkout", "-qb", "registration", self.base)
        self.add_pwrgit()
        self.commit()
        self.assertEqual(self.select(base=newer_base), ["pwrgit"])

    def test_missing_or_invalid_base_fails(self):
        for event in ["pull_request", "push"]:
            for base in ["", "does-not-exist"]:
                with self.subTest(base=base, event=event):
                    result = self.select(event, base=base, check=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
