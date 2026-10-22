#!/usr/bin/env python3
"""Reviewable dependency archive locks; fetch/verify before offline execution.

Generation is an explicit review operation, never part of a production build.
No personal Maven cache, operator configuration, or running container is read.
The TSV format is also consumed by service-dependency-lock.java (JDK only).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse
import urllib.request

MAGIC = "service-dependency-lock-v1"
HOSTS = {"repo.maven.apache.org", "deb.debian.org", "security.debian.org",
         "snapshot.debian.org", "packages.bell-sw.com"}
INPUTS = ("pom.xml", ".mvn/settings.xml", ".mvn/maven.config")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else _digest(stream)


def _digest(stream):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(chunk)
    return result.hexdigest()


def safe_path(value):
    path = PurePosixPath(value)
    if not value or str(path) != value or path.is_absolute() or any(p in {".", ".."} for p in path.parts) or "\\" in value:
        raise ValueError("Unsafe artifact path")
    return value


def safe_url(value):
    url = urllib.parse.urlsplit(value)
    if url.scheme != "https" or url.hostname not in HOSTS or url.username or url.password or url.port or url.query or url.fragment:
        raise ValueError("Unapproved artifact URL")
    return value


def load(path):
    lines = path.read_text().splitlines()
    if not lines or lines[0] != MAGIC:
        raise ValueError("Unknown lock format")
    result = {"artifacts": [], "inputs": [], "installed": []}
    seen = set()
    for line in lines[1:]:
        row = line.split("\t")
        if row[0] in {"kind", "base", "arch"} and len(row) == 2:
            if row[0] in result:
                raise ValueError("Duplicate lock metadata")
            result[row[0]] = row[1]
        elif row[0] == "input" and len(row) == 3:
            result["inputs"].append((row[1], safe_path(row[2])))
        elif row[0] == "installed" and len(row) == 3:
            result["installed"].append((row[1], row[2]))
        elif row[0] == "artifact" and len(row) == 6:
            _, sha, size, name, url, identity = row
            safe_path(name)
            safe_url(url)
            if name in seen or not re.fullmatch(r"[0-9a-f]{64}", sha) or not size.isdecimal() or int(size) <= 0:
                raise ValueError("Invalid/duplicate artifact")
            seen.add(name)
            result["artifacts"].append((sha, int(size), name, url, identity))
        else:
            raise ValueError("Malformed lock row")
    if result.get("kind") not in {"maven", "deb", "apk"} or not result["artifacts"] or not result.get("arch") or not re.fullmatch(r"docker.io/[^\s]+@sha256:[0-9a-f]{64}", result.get("base", "")):
        raise ValueError("Incomplete lock")
    if result["kind"] == "maven" and {name for _, name in result["inputs"]} != set(INPUTS):
        raise ValueError("Maven declaration inputs missing")
    return result


def check_context(lock, base, source=None):
    if lock["base"] != base:
        raise ValueError("Base image differs from reviewed dependency lock")
    if lock["kind"] == "maven":
        if source is None:
            raise ValueError("Maven source root required")
        for sha, name in lock["inputs"]:
            path = source / name
            if path.is_symlink() or not path.is_file() or digest(path) != sha:
                raise ValueError("Maven declaration changed: " + name)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Artifact redirects are not accepted")


def fetch(lock, destination):
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("Fetch destination must be empty")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def one(row):
        sha, size, name, url, _ = row
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".partial")
        h = hashlib.sha256()
        count = 0
        try:
            with opener.open(url, timeout=120) as response, partial.open("xb") as output:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    count += len(chunk)
                    if count > size:
                        raise ValueError("Artifact exceeds locked size: " + name)
                    h.update(chunk)
                    output.write(chunk)
            if count != size or h.hexdigest() != sha:
                raise ValueError("Artifact hash/size mismatch: " + name)
            partial.rename(target)
        finally:
            partial.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(one, lock["artifacts"]))
    # Only payloads live here; no unchecked resolver state or checksum sidecars.
    verify(lock, destination)


def verify(lock, destination):
    expected = {row[2] for row in lock["artifacts"]}
    actual = set()
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in artifact repository")
        if path.is_file():
            actual.add(path.relative_to(destination).as_posix())
    if actual != expected:
        raise ValueError("Missing/unreviewed artifact(s): " + ", ".join(sorted(actual ^ expected)[:8]))
    for sha, size, name, _, _ in lock["artifacts"]:
        path = destination / name
        if path.stat().st_size != size or digest(path) != sha:
            raise ValueError("Artifact hash/size mismatch: " + name)


def write_lock(path, kind, base, arch, artifacts, inputs=(), installed=()):
    rows = [MAGIC, "kind\t" + kind, "base\t" + base, "arch\t" + arch]
    rows += ["input\t" + sha + "\t" + name for sha, name in inputs]
    rows += ["installed\t" + name + "\t" + version for name, version in sorted(installed)]
    rows += ["artifact\t" + "\t".join(map(str, row)) for row in sorted(artifacts, key=lambda row: row[2])]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n")
    load(path)


def generate_maven(args):
    artifacts = []
    for path in sorted(args.repository.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlink in seed repository")
        if not path.is_file() or not (path.suffix in {".pom", ".jar"} or path.name.startswith("maven-metadata-") and path.suffix == ".xml"):
            continue
        name = path.relative_to(args.repository).as_posix()
        remote = name
        if path.name.startswith("maven-metadata-"):
            remote = str(PurePosixPath(name).parent / "maven-metadata.xml")
        if "SNAPSHOT" in name:
            raise ValueError("Snapshot dependency needs separate review")
        parts = PurePosixPath(name).parts
        identity = ":".join((".".join(parts[:-3]), parts[-3], parts[-2], parts[-1]))
        artifacts.append((digest(path), path.stat().st_size, name,
                          "https://repo.maven.apache.org/maven2/" + remote, identity))
    inputs = [(digest(args.source / name), name) for name in INPUTS]
    write_lock(args.output, "maven", args.base, "linux/aarch64", artifacts, inputs)


def generate_os(args):
    inventory = json.loads(args.inventory.read_text())
    if args.kind == "deb":
        installed = [(row["name"], row["version"]) for row in inventory["voiceOs"]["components"]]
        urls = {}
        for line in args.urls.read_text().splitlines():
            if line.startswith("'"):
                url, name, *_ = line.split()
                urls[name] = url.strip("'").replace("http://", "https://", 1)
        artifacts = []
        for path in sorted(args.archives.glob("*.deb")):
            identity = subprocess.check_output(["dpkg-deb", "-f", str(path), "Package", "Version", "Architecture"], text=True).strip().replace("\n", ";")
            artifacts.append((digest(path), path.stat().st_size, path.name, urls[path.name], identity))
    else:
        installed = [(row["packageRelease"], row["arch"]) for row in inventory["managerOs"]["components"]]
        artifacts = []
        for url in args.urls.read_text().splitlines():
            if not url.startswith("https://"):
                continue
            name = url.rsplit("/", 1)[-1]
            path = args.archives / name
            if (name.removesuffix(".apk"), "aarch64") not in installed:
                raise ValueError("APK resolver changed a recorded version: " + name)
            artifacts.append((digest(path), path.stat().st_size, name, url, name.removesuffix(".apk") + ":aarch64"))
    write_lock(args.output, args.kind, args.base, "arm64" if args.kind == "deb" else "aarch64", artifacts, installed=installed)


def install_deb(lock, destination):
    if lock["kind"] != "deb" or subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip() != lock["arch"]:
        raise ValueError("Wrong OS lock/architecture")
    verify(lock, destination)
    # dpkg consumes only these verified local archives; no package resolver or
    # repository is available to add an unreviewed transitive package.
    subprocess.run(["dpkg", "--unpack",
                    *[str((destination / row[2]).resolve()) for row in lock["artifacts"]]],
                   check=True, env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
    subprocess.run(["dpkg", "--configure", "--pending"], check=True,
                   env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
    if subprocess.check_output(["dpkg", "--audit"], text=True).strip():
        raise ValueError("Installed package configuration is incomplete")
    installed = subprocess.check_output(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"], text=True)
    if set(tuple(line.split("\t")) for line in installed.splitlines()) != set(lock["installed"]):
        raise ValueError("Installed OS identities differ from reviewed inventory")


def resolve_deb(args):
    """Explicit review-time acquisition, using signed apt indexes and old versions."""
    inventory = json.loads(args.inventory.read_text())
    selected = [row["name"] + "=" + row["version"] for row in inventory["voiceOs"]["components"]]
    args.archives.mkdir(parents=True, exist_ok=False)
    subprocess.run(["apt-get", "update"], check=True)
    options = ["apt-get", "-y", "--no-install-recommends", "--download-only",
               "-o", "Dir::Cache::archives=" + str(args.archives)]
    plan = subprocess.check_output([*options, "--print-uris", "install", *selected], text=True)
    args.urls.write_text(plan)
    subprocess.run([*options, "install", *selected], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "verify", "install-deb"):
        p = sub.add_parser(name)
        p.add_argument("lock", type=Path)
        p.add_argument("directory", type=Path)
        p.add_argument("--base", required=True)
        p.add_argument("--source", type=Path)
    p = sub.add_parser("generate-maven")
    p.add_argument("--repository", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("resolve-deb")
    for name in ("inventory", "archives", "urls"):
        p.add_argument("--" + name, type=Path, required=True)
    p = sub.add_parser("generate-os")
    p.add_argument("--kind", choices=("deb", "apk"), required=True)
    for name in ("inventory", "urls", "archives", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--base", required=True)
    args = parser.parse_args()
    try:
        if args.command == "generate-maven":
            generate_maven(args)
        elif args.command == "generate-os":
            generate_os(args)
        elif args.command == "resolve-deb":
            resolve_deb(args)
        else:
            lock = load(args.lock)
            check_context(lock, args.base, args.source)
            {"fetch": fetch, "verify": verify, "install-deb": install_deb}[args.command](lock, args.directory)
        print("Dependency lock: " + args.command + " passed")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Dependency lock rejected: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
