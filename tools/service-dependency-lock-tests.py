#!/usr/bin/env python3
"""Offline regression tests for lock validation and pre-build boundaries."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dependency_lock", HERE / "service-dependency-lock.py")
locktool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(locktool)
BASE = "docker.io/library/maven@sha256:" + "a" * 64


class LockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository"
        self.repo.mkdir()
        self.artifact = self.repo / "g/a/1/a-1.jar"
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_bytes(b"reviewed")
        self.source = self.root / "source"
        for name in locktool.INPUTS:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("public fixture\n")
        self.file = self.root / "test.lock"
        locktool.write_lock(self.file, "maven", BASE, "linux/aarch64",
                            [(locktool.digest(self.artifact), 8, "g/a/1/a-1.jar",
                              "https://repo.maven.apache.org/maven2/g/a/1/a-1.jar", "g:a:1:jar")],
                            [(locktool.digest(self.source / name), name) for name in locktool.INPUTS])
        self.lock = locktool.load(self.file)

    def test_valid_repository(self):
        locktool.check_context(self.lock, BASE, self.source)
        locktool.verify(self.lock, self.repo)

    def test_same_size_tamper_rejected_before_execution(self):
        self.artifact.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "hash/size"):
            locktool.verify(self.lock, self.repo)

    def test_missing_rejected(self):
        self.artifact.unlink()
        with self.assertRaisesRegex(ValueError, "Missing/unreviewed"):
            locktool.verify(self.lock, self.repo)

    def test_unreviewed_rejected(self):
        (self.repo / "unreviewed.jar").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "Missing/unreviewed"):
            locktool.verify(self.lock, self.repo)

    def test_symlink_rejected(self):
        self.artifact.unlink()
        self.artifact.symlink_to(self.source / "pom.xml")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            locktool.verify(self.lock, self.repo)

    def test_changed_pom_requires_review(self):
        (self.source / "pom.xml").write_text("changed")
        with self.assertRaisesRegex(ValueError, "declaration changed"):
            locktool.check_context(self.lock, BASE, self.source)

    def test_changed_base_requires_review(self):
        with self.assertRaisesRegex(ValueError, "Base image"):
            locktool.check_context(self.lock, BASE.replace("a" * 64, "b" * 64), self.source)

    def test_fetch_does_not_reuse_existing_cache(self):
        with self.assertRaisesRegex(ValueError, "must be empty"):
            locktool.fetch(self.lock, self.repo)

    def test_paths_rejected(self):
        for name in ("../escape", "/absolute", "x/../escape", "x//y", "x\\y"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                locktool.safe_path(name)

    def test_urls_rejected(self):
        for url in ("http://repo.maven.apache.org/a", "https://repo.maven.apache.org.evil/a",
                    "https://user:pass@repo.maven.apache.org/a", "https://repo.maven.apache.org:443/a",
                    "https://repo.maven.apache.org/a?x=1", "https://repo.maven.apache.org/a#x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                locktool.safe_url(url)

    def test_redirect_rejected(self):
        with self.assertRaisesRegex(ValueError, "redirects"):
            locktool.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")

    def test_duplicate_artifact_rejected(self):
        row = self.file.read_text().splitlines()[-1]
        self.file.write_text(self.file.read_text() + row + "\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            locktool.load(self.file)

    def test_missing_input_rejected(self):
        self.file.write_text("\n".join(row for row in self.file.read_text().splitlines() if not row.endswith("\tpom.xml")) + "\n")
        with self.assertRaisesRegex(ValueError, "inputs missing"):
            locktool.load(self.file)

    def test_deb_invalid_inputs_stop_before_installer(self):
        self.lock["kind"] = "deb"
        self.lock["arch"] = "arm64"
        for case in ("tamper", "missing", "unreviewed"):
            with self.subTest(case=case):
                self.artifact.write_bytes(b"reviewed")
                if case == "tamper":
                    self.artifact.write_bytes(b"tampered")
                elif case == "missing":
                    self.artifact.unlink()
                else:
                    (self.repo / "unreviewed.deb").write_bytes(b"unknown")
                with patch.object(locktool.subprocess, "check_output", return_value="arm64\n"), patch.object(locktool.subprocess, "run") as run:
                    with self.assertRaises(ValueError):
                        locktool.install_deb(self.lock, self.repo)
                    run.assert_not_called()

    def test_checked_in_locks_are_complete_and_current(self):
        root = HERE.parent
        for name, kind in (("maven-linux-aarch64.lock", "maven"), ("voice-deb-arm64.lock", "deb"), ("manager-apk-aarch64.lock", "apk")):
            with self.subTest(name=name):
                lock = locktool.load(HERE / "dependency-locks" / name)
                self.assertEqual(kind, lock["kind"])
                if kind == "maven":
                    locktool.check_context(lock, lock["base"], root / "main/manager-api")
                    self.assertTrue(any("maven-compiler-plugin" in row[2] for row in lock["artifacts"]))
                    self.assertTrue(any("spring-boot-maven-plugin" in row[2] for row in lock["artifacts"]))
                else:
                    self.assertTrue(lock["installed"])

    def test_dockerfiles_enforce_before_offline_build(self):
        web = (HERE.parent / "Dockerfile-web").read_text()
        voice = (HERE.parent / "Dockerfile-server-base").read_text()
        self.assertIn("RUN --network=none java", web)
        self.assertIn("npm ci --ignore-scripts", web)
        self.assertIn("RUN --network=none npm run build", web)
        self.assertIn("mvn -o -B", web)
        self.assertLess(web.index("java /opt/service-dependency-lock.java verify"), web.index("mvn -o -B"))
        self.assertNotIn("apk update", web)
        self.assertIn("RUN --network=none sh /opt/service-dependency-lock-apk.sh", web)
        self.assertIn("RUN --network=none python /opt/service-dependency-lock.py install-deb", voice)
        self.assertNotIn("apt-get update", voice)

    def test_os_versions_and_runtime_hashes_preserve_baseline(self):
        inventory = json.loads((HERE.parent / "docs/maintenance/service-build-components.json").read_text())
        deb = locktool.load(HERE / "dependency-locks/voice-deb-arm64.lock")
        apk = locktool.load(HERE / "dependency-locks/manager-apk-aarch64.lock")
        maven = locktool.load(HERE / "dependency-locks/maven-linux-aarch64.lock")
        self.assertEqual(set(deb["installed"]), {(r["name"], r["version"]) for r in inventory["voiceOs"]["components"]})
        self.assertEqual(set(apk["installed"]), {(r["packageRelease"], r["arch"]) for r in inventory["managerOs"]["components"]})
        # Every pre-migration bundled Java library must be present byte-for-byte
        # in the input lock, not only a post-build inventory.
        recorded = next(value for value in inventory.values() if isinstance(value, dict) and "components" in value and any("path" in row and row["path"].startswith("BOOT-INF/lib/") for row in value["components"]))
        hashes = {row[0] for row in maven["artifacts"]}
        embedded = json.loads((HERE / "dependency-locks/maven-embedded.json").read_text())
        self.assertTrue(any(row[2] == embedded["container"] and row[0] == embedded["containerSha256"] for row in maven["artifacts"]))
        hashes.add(embedded["sha256"])
        for component in recorded["components"]:
            self.assertTrue(component["sha256"] in hashes, component["path"])


if __name__ == "__main__":
    unittest.main()
