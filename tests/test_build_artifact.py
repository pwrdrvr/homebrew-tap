"""No release HTTP fallback, exact release-build provenance, verified ZIP members."""
import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("artifact", ROOT / "scripts/build-artifact.py")
artifact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact)


class BuildArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "installer.dmg"
        self.payload = b"signed installer"
        self.sha = hashlib.sha256(self.payload).hexdigest()
        self.commit = "a" * 40
        self.run = dict(id=10, head_sha=self.commit, status="completed", conclusion="success", event="push",
                        path=".github/workflows/release.yml", head_branch="v1.2.3",
                        head_repository=dict(full_name="pwrdrvr/PwrSnap"))
        self.archive = dict(id=20, name="desktop-release-macos-artifacts", expired=False)
        self.jobs = []
        self.url = "https://github.com/pwrdrvr/PwrSnap/releases/download/v1.2.3/PwrSnap-1.2.3-universal.dmg"
        self.calls = []

    def read(self, endpoint):
        self.calls.append(endpoint)
        self.assertNotIn("releases/download", endpoint)
        self.assertNotIn("releases/assets", endpoint)
        if "/git/ref/" in endpoint:
            return dict(object=dict(type="commit", sha=self.commit))
        if "/workflows/" in endpoint:
            return dict(workflow_runs=[self.run])
        if "/jobs?" in endpoint:
            self.assertIn("filter=all", endpoint)
            return dict(jobs=self.jobs)
        return dict(artifacts=[self.archive])

    def download(self, repo, selected, target):
        self.assertEqual(selected["id"], 20)
        with zipfile.ZipFile(target, "w") as bundle:
            bundle.writestr("dist/PwrSnap-1.2.3-universal.dmg", self.payload)

    def acquire(self):
        return artifact.acquire(self.url, self.sha, len(self.payload), self.target, self.read, self.download)

    def test_cold_build_artifact_then_warm_cache_has_no_network(self):
        self.assertEqual(self.acquire(), "build-artifact")
        self.assertEqual(self.target.read_bytes(), self.payload)
        count = len(self.calls)
        self.assertEqual(self.acquire(), "restored")
        self.assertEqual(len(self.calls), count)

    def pwragent_failed_run(self):
        # v1.3.13 published signed desktop assets, then failed npm verification.
        self.run.update(conclusion="failure", head_branch="v1.3.13",
                        head_repository=dict(full_name="pwrdrvr/PwrAgent"))
        self.archive["name"] = "desktop-release-artifacts"
        self.url = "https://github.com/pwrdrvr/PwrAgent/releases/download/v1.3.13/PwrAgent-1.3.13-arm64.dmg"
        self.jobs = [dict(name=name, status="completed", conclusion=conclusion, run_attempt=2)
                     for name, conclusion in [
                         ("Sign, notarize, package macOS", "success"),
                         ("Sign and package Windows installer", "success"),
                         ("Publish release assets", "success"),
                         ("Verify Outpost npm publication after processing", "failure"),
                         ("Verify desktop and Outpost release completion", "failure")]]

    def test_published_desktop_artifact_survives_unrelated_npm_failure(self):
        self.pwragent_failed_run()
        def download(repo, selected, target):
            self.assertEqual(repo, "pwrdrvr/PwrAgent")
            self.assertEqual(selected["id"], 20)
            with zipfile.ZipFile(target, "w") as bundle:
                bundle.writestr("dist/PwrAgent-1.3.13-arm64.dmg", self.payload)
        self.assertEqual(artifact.acquire(self.url, self.sha, len(self.payload), self.target,
                                          self.read, download), "build-artifact")
        self.assertEqual(self.target.read_bytes(), self.payload)
        self.assertTrue(any("status=completed" in call for call in self.calls))

    def test_failed_run_requires_successful_producer_and_publication(self):
        self.pwragent_failed_run()
        for name in ["Sign, notarize, package macOS", "Publish release assets"]:
            job = next(job for job in self.jobs if job["name"] == name)
            for conclusion in ["failure", "skipped", "cancelled", None]:
                with self.subTest(name=name, conclusion=conclusion):
                    job["conclusion"] = conclusion
                    with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
                        self.acquire()
            job["conclusion"] = "success"
            self.jobs.remove(job)
            with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
                self.acquire()
            self.jobs.append(job)
        self.assertFalse(self.target.exists())

    def test_latest_required_job_attempt_controls_failed_run_eligibility(self):
        self.pwragent_failed_run()
        producer = next(job for job in self.jobs if job["name"] == "Sign, notarize, package macOS")
        # Failed/skipped jobs from the original attempt do not veto a good retry.
        self.jobs.insert(0, dict(producer, conclusion="skipped", run_attempt=1))
        self.assertEqual(artifact.select_artifact("pwrdrvr/PwrAgent", "v1.3.13",
                                                  "PwrAgent-1.3.13-arm64.dmg", self.read)["artifact"]["id"], 20)
        # A later failed retry must not be hidden by an earlier success.
        self.jobs.append(dict(producer, conclusion="failure", run_attempt=3))
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            self.acquire()
        self.jobs[-1].update(conclusion="success", status="in_progress")
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            self.acquire()
        # Duplicate required names in one attempt cannot identify the producer.
        self.jobs[-1].update(run_attempt=2, status="completed")
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            self.acquire()

    def test_failed_run_checks_the_selected_platform_or_assembled_producer(self):
        self.pwragent_failed_run()
        self.jobs[0]["conclusion"] = "failure"
        for name, member in [("windows-installer", "PwrAgent-1.3.13-windows-x64-setup.exe"),
                             ("release-publish-artifacts", "PwrAgent-1.3.13-arm64.dmg")]:
            with self.subTest(name=name):
                self.archive["name"] = name
                selected = artifact.select_artifact("pwrdrvr/PwrAgent", "v1.3.13", member, self.read)
                self.assertEqual(selected["artifact"]["id"], 20)
        self.archive["name"] = "windows-installer"
        self.jobs[1]["conclusion"] = "failure"
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            artifact.select_artifact("pwrdrvr/PwrAgent", "v1.3.13",
                                     "PwrAgent-1.3.13-windows-x64-setup.exe", self.read)

    def test_failed_run_still_requires_trusted_provenance_and_matching_bytes(self):
        self.pwragent_failed_run()
        for key, value in [("event", "pull_request"), ("head_sha", "b" * 40),
                           ("status", "in_progress"), ("conclusion", "cancelled"),
                           ("path", ".github/workflows/preview-build.yml"),
                           ("head_branch", "main"), ("head_repository", dict(full_name="attacker/fork"))]:
            with self.subTest(key=key):
                original = self.run[key]
                self.run[key] = value
                with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
                    self.acquire()
                self.run[key] = original
        self.archive["expired"] = True
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            self.acquire()
        self.archive["expired"] = False
        def corrupt(repo, selected, target):
            with zipfile.ZipFile(target, "w") as bundle:
                bundle.writestr("PwrAgent-1.3.13-arm64.dmg", b"x" * len(self.payload))
        with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
            artifact.acquire(self.url, self.sha, len(self.payload), self.target, self.read, corrupt)
        self.assertFalse(self.target.exists())

    def test_required_jobs_are_found_after_first_page(self):
        self.pwragent_failed_run()
        def read(endpoint):
            if "/jobs?" in endpoint and endpoint.endswith("&page=1"):
                self.calls.append(endpoint)
                return dict(jobs=[self.jobs[-1]] * 100)
            return self.read(endpoint)
        self.assertEqual(artifact.select_artifact("pwrdrvr/PwrAgent", "v1.3.13",
                                                  "PwrAgent-1.3.13-arm64.dmg", read)["artifact"]["id"], 20)
        self.assertTrue(any("/jobs?" in call and "page=2" in call for call in self.calls))

    def test_other_products_use_their_desktop_publication_job(self):
        self.run["conclusion"] = "failure"
        self.jobs = [dict(name=name, status="completed", conclusion="success", run_attempt=1)
                     for name in ["Sign, notarize, package macOS", "Create release and publish platform assets"]]
        for repo in ["pwrdrvr/PwrGit", "pwrdrvr/PwrSnap"]:
            with self.subTest(repo=repo):
                self.run["head_repository"]["full_name"] = repo
                self.assertEqual(artifact.select_artifact(repo, "v1.2.3", "installer.dmg", self.read)
                                 ["artifact"]["id"], 20)

    def test_untrusted_failed_wrong_commit_workflow_or_branch_cannot_supply_bytes(self):
        for key, value in [("event", "pull_request"), ("conclusion", "failure"),
                           ("status", "in_progress"), ("conclusion", "cancelled"),
                           ("head_sha", "b" * 40), ("path", ".github/workflows/preview-build.yml"),
                           ("head_branch", "main"), ("head_repository", dict(full_name="attacker/fork"))]:
            with self.subTest(key=key):
                original = self.run[key]
                self.run[key] = value
                with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
                    self.acquire()
                self.run[key] = original
        self.assertFalse(self.target.exists())

    def test_expired_missing_artifacts_and_corrupt_cache_fail_closed(self):
        self.archive["expired"] = True
        with self.assertRaisesRegex(ValueError, "fallback is prohibited"):
            self.acquire()
        self.target.write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
            self.acquire()

    def test_wrong_bytes_duplicate_and_traversal_members_never_promote(self):
        archive = self.target.with_suffix(".zip")
        name = "PwrSnap-1.2.3-universal.dmg"
        for members in [{name: b"wrong installer!"}, {name: self.payload, "dist/" + name: self.payload},
                        {"../" + name: self.payload}]:
            with self.subTest(members=list(members)):
                with zipfile.ZipFile(archive, "w") as bundle:
                    for path, content in members.items():
                        bundle.writestr(path, content)
                with self.assertRaises(ValueError):
                    artifact.extract(archive, name, self.target, self.sha, len(self.payload))

    def test_annotated_tag_and_moved_tag(self):
        def annotated(endpoint):
            if "/git/ref/" in endpoint:
                return dict(object=dict(type="tag", sha="b" * 40))
            return dict(object=dict(type="commit", sha=self.commit))
        self.assertEqual(artifact.tag_commit("pwrdrvr/PwrSnap", "v1.2.3", annotated), self.commit)
        def moved(repo, selected, target):
            self.download(repo, selected, target)
            self.commit = "c" * 40
        with self.assertRaisesRegex(ValueError, "tag changed"):
            artifact.acquire(self.url, self.sha, len(self.payload), self.target, self.read, moved)
        self.assertFalse(self.target.exists())

    def test_windows_checksum_rename_is_verified(self):
        archive = self.target.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("SHA256SUMS", self.payload)
        artifact.extract(archive, "PwrAgent-windows-SHA256SUMS", self.target, self.sha, len(self.payload))
        self.assertEqual(self.target.read_bytes(), self.payload)

    def test_homebrew_curl_guard_blocks_release_and_release_asset_api(self):
        for url in [self.url, "https://api.github.com/repos/pwrdrvr/PwrSnap/releases/assets/123"]:
            result = subprocess.run([str(ROOT / "scripts/ci-curl.py"), "-L", url], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("blocked in CI", result.stderr)
