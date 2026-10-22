#!/usr/bin/env python3
"""Compare exported public build artifacts/package identities, never live data.

JAR inspection reads library entries and their hashes, not application classes or
configuration. Export inputs only from new disposable locked-image containers.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def compare(args):
    inventory = json.loads((ROOT / "docs/maintenance/service-build-components.json").read_text())
    result = {}
    if args.manager_jar:
        recorded = next(value for value in inventory.values() if isinstance(value, dict) and "components" in value and any(row.get("path", "").startswith("BOOT-INF/lib/") for row in value["components"]))
        expected = {row["path"]: row["sha256"] for row in recorded["components"]}
        with zipfile.ZipFile(args.manager_jar) as jar:
            actual = {name: hashlib.sha256(jar.read(name)).hexdigest() for name in jar.namelist()
                      if name.startswith("BOOT-INF/lib/") and name.endswith(".jar")}
            if actual != expected:
                raise ValueError("Manager library names/hashes changed")
            if any(PurePosixPath(name).name.startswith("application-") and name.endswith((".yml", ".yaml")) for name in jar.namelist()):
                raise ValueError("Operator profile entry found (contents not opened)")
        result["managerJavaLibrariesPreserved"] = len(expected)
        result["operatorProfileEntries"] = 0
    if args.manager_os:
        expected = {row["packageRelease"] for row in inventory["managerOs"]["components"]}
        if set(args.manager_os.read_text().splitlines()) != expected:
            raise ValueError("Manager installed OS identities changed")
        result["managerOsPackagesPreserved"] = len(expected)
    if args.voice_os:
        expected = {(row["name"], row["version"]) for row in inventory["voiceOs"]["components"]}
        actual = {tuple(line.split("\t")) for line in args.voice_os.read_text().splitlines()}
        if actual != expected:
            raise ValueError("Voice installed OS identities changed")
        result["voiceOsPackagesPreserved"] = len(expected)
    if args.voice_python:
        baseline = json.loads((ROOT / "docs/maintenance/service-python-sbom.json").read_text())
        canonical = lambda name: re.sub(r"[-_.]+", "-", name).lower()
        expected = {(canonical(row["name"]), row["version"]) for row in baseline["components"]}
        actual = {(canonical(row["name"]), row["version"]) for row in json.loads(args.voice_python.read_text())}
        if actual != expected:
            raise ValueError("Voice installed Python versions changed")
        result["voicePythonPackagesPreserved"] = len(expected)
    if args.maven_repository:
        embedded = json.loads((ROOT / "tools/dependency-locks/maven-embedded.json").read_text())
        container = args.maven_repository / embedded["container"]
        if hashlib.sha256(container.read_bytes()).hexdigest() != embedded["containerSha256"]:
            raise ValueError("Embedded Maven parent archive changed")
        with zipfile.ZipFile(container) as jar:
            if hashlib.sha256(jar.read(embedded["entry"])).hexdigest() != embedded["sha256"]:
                raise ValueError("Embedded Maven runtime artifact changed")
        result["embeddedMavenRuntimeArtifactPreserved"] = True
    if not result:
        raise ValueError("Supply at least one public export")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manager-jar", "manager-os", "voice-os", "voice-python", "maven-repository"):
        parser.add_argument("--" + name, type=Path)
    try:
        print(json.dumps(compare(parser.parse_args()), indent=2))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print("Component preservation failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
