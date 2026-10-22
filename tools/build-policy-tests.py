#!/usr/bin/env python3
"""Synthetic offline checks only. Compose config never contacts the Docker daemon."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_inputs", ROOT / "tools/build-inputs.py")
inputs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inputs)
COMPOSE = next((str(path) for path in (
    Path(shutil.which("docker-compose") or "/nonexistent-compose"),
    Path("/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose"),
    Path("/opt/homebrew/lib/docker/cli-plugins/docker-compose"),
    Path("/usr/local/lib/docker/cli-plugins/docker-compose"),
    Path.home() / ".docker/cli-plugins/docker-compose",
) if path.is_file() and os.access(path, os.X_OK)), None)


class ImageInputs(unittest.TestCase):
    def test_all_reviewed_roles_require_full_digest(self):
        for role, repository in inputs.REPOSITORIES.items():
            value = repository + ":test@sha256:" + "a" * 64
            self.assertEqual(inputs.validate_image(role, value), value)

    def test_reject_unpinned_mirror_or_wrong_repository(self):
        for value in ["python:3.10", "docker.io/library/python:3.10", "ghcr.io/other/python@sha256:" + "a" * 64,
                      "docker.io.bad.test/library/python@sha256:" + "a" * 64,
                      "docker.io/library/node@sha256:" + "a" * 64,
                      "docker.io/library/python@sha256:short"]:
            with self.assertRaises(ValueError):
                inputs.validate_image("python", value)

    def test_rejection_redacts_input(self):
        with self.assertRaises(ValueError) as caught:
            inputs.validate_image("python", "https://secret@unknown.test/private")
        self.assertNotIn("secret", str(caught.exception))
        self.assertNotIn("unknown.test", str(caught.exception))

    def test_missing_and_empty_inputs_fail(self):
        for args in [("images",), ("images", "--python-image", "")]:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(inputs.main(args), 1)

    def test_source_report_uses_only_fixed_public_files(self):
        report = inputs.source_report()
        self.assertEqual(report["kind"], "source-input-manifest")
        self.assertEqual(len(report["files"]), len(inputs.SOURCES))
        for item in report["files"]:
            self.assertRegex(item["sha256"], r"^[a-f0-9]{64}$")
            self.assertNotIn(".env", item["path"])
            self.assertNotIn(".config.yaml", item["path"])
        self.assertTrue(report["limitations"])


class SourceSurfaces(unittest.TestCase):
    def test_python_ci_prepares_the_config_required_by_logging(self):
        workflow = (ROOT / ".github/workflows/test.yml").read_text()
        step = workflow.split("      - name: Run focused offline configuration and core tests\n", 1)[1]
        step = step.split("\n  java:", 1)[0]
        configured = re.search(r"^          PYTEST_CONFIG_FILE: (.+)$", step, re.M).group(1)
        command = next(line.strip() for line in step.splitlines()
                       if line.strip().startswith("python -c "))
        argv = shlex.split(command)
        self.assertEqual(argv[:2], ["python", "-c"])
        self.assertIn("RUN_LIVE_API_TESTS: '0'", step)
        self.assertIn("python -B -m pytest tests/config tests/core -x -q", step)
        with tempfile.TemporaryDirectory(prefix="ci-config-fixture-") as directory:
            root = Path(directory)
            runner = root / "runner"
            runner.mkdir()
            # Interpret only the old runner-temp expression inside our own fixture.
            config = configured.replace("${{ runner.temp }}", str(runner))
            env = {"PATH": os.defpath, "PYTEST_CONFIG_FILE": config, "RUN_LIVE_API_TESTS": "0"}
            result = subprocess.run([sys.executable, *argv[1:]], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = root / "data/.config.yaml"
            self.assertTrue(expected.is_file(), "CI must prepare the path checked by logging")
            self.assertEqual((root / config).resolve(), expected.resolve())
            fixture = expected.read_bytes()
            self.assertIn(b"manager-api: {url: null, secret: null}", fixture)
            self.assertNotIn(b"http", fixture)
            # Preparing a clean CI fixture must not overwrite an existing config.
            repeated = subprocess.run([sys.executable, *argv[1:]], cwd=root, env=env,
                                      capture_output=True, text=True, timeout=10)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(expected.read_bytes(), fixture)

    def test_no_legacy_build_hosts_or_mandatory_asr_mounts(self):
        paths = [ROOT / name for name in ("Dockerfile-server", "Dockerfile-server-base", "Dockerfile-web", "docker-setup.sh")]
        paths += list((ROOT / ".github/workflows").glob("*.yml"))
        paths += list((ROOT / "main/xiaozhi-server").glob("docker-compose*.yml"))
        forbidden = r"ghcr\.nju|ghfast\.|ghproxy\.|mirrors\.aliyun|trusted-host|modelscope\.cn|SenseVoiceSmall/model\.pt"
        for path in paths:
            self.assertNotRegex(path.read_text(), forbidden, str(path.relative_to(ROOT)))

    def test_docker_from_requires_explicit_input(self):
        for name in ("Dockerfile-server", "Dockerfile-server-base", "Dockerfile-web"):
            text = (ROOT / name).read_text()
            for image in re.findall(r"^FROM (\S+)", text, re.M):
                self.assertRegex(image, r"^\$\{[A-Z_]+\}$")
        self.assertIn("ARG SERVER_BASE_IMAGE", (ROOT / "Dockerfile-server").read_text())

    def test_web_copies_maven_policy_and_checks_lock_before_install(self):
        text = (ROOT / "Dockerfile-web").read_text()
        self.assertIn("COPY main/manager-api/.mvn ./.mvn", text)
        self.assertIn("--settings .mvn/settings.xml", text)
        self.assertLess(text.index("node /opt/build-npm-lock.mjs"), text.index("npm ci"))
        self.assertIn("VUE_APP_USE_CDN=false", text)

    def test_python_installs_only_pinned_hashed_binary_dependencies(self):
        dockerfile = (ROOT / "Dockerfile-server-base").read_text()
        self.assertIn("main/xiaozhi-server/requirements.lock", dockerfile)
        self.assertIn("--require-hashes -r requirements.lock", dockerfile)
        self.assertIn("--only-binary=:all:", dockerfile)
        lock = (ROOT / "main/xiaozhi-server/requirements.lock").read_text()
        logical = re.sub(r"\\\n\s*", " ", lock)
        requirements = [line.strip() for line in logical.splitlines()
                        if line.strip() and not line.lstrip().startswith("#")]
        self.assertTrue(requirements)
        for requirement in requirements:
            self.assertRegex(requirement, r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^\s;*]+")
            self.assertRegex(requirement, r"--hash=sha256:[a-f0-9]{64}(?:\s|$)")
            self.assertNotIn("://", requirement)

    def test_context_excludes_private_and_legacy_model_inputs(self):
        text = (ROOT / ".dockerignore").read_text()
        for rule in ["**/.env", "**/.env.*", "main/xiaozhi-server/data/", "main/xiaozhi-server/models/**",
                     "main/xiaozhi-server/models/SenseVoiceSmall/"]:
            self.assertIn(rule, text)
        self.assertIn("!main/xiaozhi-server/models/snakers4_silero-vad/**", text)

    def test_retired_benchmark_has_no_config_or_provider_import(self):
        path = ROOT / "main/xiaozhi-server/performance_tester.py"
        tree = ast.parse(path.read_text())
        imported = [item.name for node in ast.walk(tree) if isinstance(node, ast.Import) for item in node.names]
        self.assertEqual(imported, ["sys"])
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)))
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-B", str(path)], cwd=directory,
                                    capture_output=True, text=True, env={"PATH": os.defpath}, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unavailable", result.stderr)
        self.assertEqual(list((ROOT / "main/xiaozhi-server/performance_tester").glob("*.py")), [])

    def test_setup_has_only_non_mutating_paths(self):
        path = ROOT / "docker-setup.sh"
        subprocess.run(["/bin/sh", "-n", str(path)], check=True, timeout=10)
        for args, expected in [([], 0), (["--help"], 0), (["--install"], 2)]:
            result = subprocess.run(["/bin/sh", str(path), *args], capture_output=True, text=True,
                                    env={"PATH": "/nonexistent"}, timeout=10)
            self.assertEqual(result.returncode, expected)
            self.assertIn("No Docker daemon settings", result.stdout)


@unittest.skipUnless(COMPOSE, "Docker Compose plugin executable not installed; no daemon is required")
class ComposeSyntax(unittest.TestCase):
    def config(self, name, missing=False):
        with tempfile.TemporaryDirectory(prefix="build-policy-") as directory:
            env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": directory,
                   "DOCKER_CONFIG": directory, "SERVER_IMAGE": "xiaozhi-local/server:fixture",
                   "SERVER_BASE_IMAGE": "xiaozhi-local/server-base:fixture", "WEB_IMAGE": "xiaozhi-local/web:fixture",
                   "CANDIDATE_DATA_DIR": directory, "CANDIDATE_DB_PASSWORD": "synthetic-only-not-real",
                   "NPM_REGISTRY": "https://registry.npmjs.org"}
            for role, repository in inputs.REPOSITORIES.items():
                env[role.upper() + "_IMAGE"] = repository + "@sha256:" + "a" * 64
            if missing:
                env.pop("SERVER_IMAGE")
            return subprocess.run([COMPOSE, "--env-file", "/dev/null",
                                   "-p", "build-policy-fixture", "-f", str(ROOT / "main/xiaozhi-server" / name),
                                   "config", "--format", "json"], env=env, capture_output=True, text=True, timeout=20)

    def test_both_compose_templates_parse_with_synthetic_inputs(self):
        for name in ("docker-compose.yml", "docker-compose_all.yml"):
            result = self.config(name)
            self.assertEqual(result.returncode, 0, result.stderr)
            services = json.loads(result.stdout)["services"]
            for service in services.values():
                self.assertNotIn("container_name", service)
                for port in service.get("ports", []):
                    self.assertEqual(port["host_ip"], "127.0.0.1")
                for volume in service.get("volumes", []):
                    self.assertNotIn("SenseVoice", volume.get("target", ""))
            self.assertEqual(services["xiaozhi-esp32-server"]["pull_policy"], "never")

    def test_missing_explicit_image_fails_before_use(self):
        for name in ("docker-compose.yml", "docker-compose_all.yml"):
            result = self.config(name, missing=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SERVER_IMAGE", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
