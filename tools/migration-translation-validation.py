#!/usr/bin/env python3
"""Prove translation migration equivalence using ONLY disposable Docker fixtures.

Requires a newly created, internal network and mysql:8.4 server aliased as
migration-db, with empty migration_baseline/current/upgrade databases. No ports,
user database mounts, application startup, SQL rewrites, or checksum resets.
The caller owns infrastructure lifecycle; this harness removes only its runners.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BASE = "eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b"
RES = "main/manager-api/src/main/resources"
IMAGE = "maven:3.9.11-eclipse-temurin-21"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
ET.register_namespace("", NS["m"])


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", required=True)
    parser.add_argument("--cache", default="/private/tmp/xiaozhi-translation-m2")
    parser.add_argument("--settings", default="/private/tmp/xiaozhi-maven-test-settings.xml")
    parser.add_argument("--report", default="/private/tmp/xiaozhi-migration-validation.md")
    args = parser.parse_args()
    network = json.loads(subprocess.check_output(["docker", "network", "inspect", args.network]))[0]
    if not network["Internal"] or network["Labels"].get("xiaozhi.validation") != "migration-translation-20261020":
        raise SystemExit("Refusing a network not explicitly created for this validation")
    work = Path(tempfile.mkdtemp(prefix="xiaozhi-migration-proof-", dir="/private/tmp"))
    report = ["# Migration translation validation", "", "Baseline: " + BASE,
              "Artifacts: " + str(work), "Image: " + IMAGE,
              "Network: " + args.network, "No host ports or existing databases used.", ""]
    try:
        protected = json.loads((ROOT / "docs/maintenance/english-baseline.json").read_text())["protectedHashes"]
        for rel, expected in protected.items():
            old = subprocess.check_output(["git", "show", BASE + ":" + rel], cwd=ROOT)
            assert digest(old) == expected == digest((ROOT / rel).read_bytes()), rel
        report.append("PASS: all %d protected SHA-256 hashes match baseline and current bytes." % len(protected))
        paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, RES + "/db/changelog"], cwd=ROOT).decode().splitlines()
        for rel in paths:
            relative = Path(rel).relative_to(RES)
            for flavor in ("baseline", "current"):
                dest = work / flavor / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                data = subprocess.check_output(["git", "show", BASE + ":" + rel], cwd=ROOT) if flavor == "baseline" else (ROOT / rel).read_bytes()
                dest.write_bytes(data)
        before_hashes = {rel: digest((ROOT / rel).read_bytes()) for rel in paths}
        count = len(re.findall(r"^\s+path: classpath:", (work / "current/db/changelog/db.changelog-master.yaml").read_text(), re.M))
        report.append("Master SQL references: %d; immutable resource files: %d." % (count, len(paths)))
        shutil.copytree(args.cache, work / "m2")
        shutil.copy2(args.settings, work / "settings.xml")
        shutil.copy2(ROOT / "tools/migration-translation-validation.java", work / "MigrationTranslationValidation.java")
        # Reuse the actual POM parent/properties and migration/driver dependencies,
        # plus Spring Core for the application's classpath resource accessor.
        # Parent dependency management supplies the application's exact transitive versions.
        for flavor in ("baseline", "current"):
            raw = subprocess.check_output(["git", "show", BASE + ":main/manager-api/pom.xml"], cwd=ROOT) if flavor == "baseline" else (ROOT / "main/manager-api/pom.xml").read_bytes()
            pom = ET.fromstring(raw)
            minimal = ET.Element("{" + NS["m"] + "}project")
            ET.SubElement(minimal, "modelVersion").text = "4.0.0"
            minimal.append(pom.find("m:parent", NS))
            for tag, value in (("groupId", "validation"), ("artifactId", "migration-proof"), ("version", "1")):
                ET.SubElement(minimal, tag).text = value
            minimal.append(pom.find("m:properties", NS))
            deps = ET.SubElement(minimal, "dependencies")
            for dep in pom.findall("m:dependencies/m:dependency", NS):
                if dep.find("m:artifactId", NS).text in ("liquibase-core", "mysql-connector-j"):
                    deps.append(dep)
            spring = ET.SubElement(deps, "dependency")
            ET.SubElement(spring, "groupId").text = "org.springframework"
            ET.SubElement(spring, "artifactId").text = "spring-core"
            ET.ElementTree(minimal).write(work / (flavor + ".pom.xml"), encoding="utf-8", xml_declaration=True)

        def docker(command, log, resources="current"):
            name = "xiaozhi-proof-runner-" + work.name.rsplit("-", 1)[1]
            cmd = ["docker", "run", "--rm", "--name", name, "--network", args.network,
                   "--label", "xiaozhi.validation=migration-translation-20261020",
                   "-e", "MYSQL_PWD=disposable-validation-only", "-v", str(work) + ":/work",
                   "-w", "/work", IMAGE, "sh", "-ec", command]
            with (work / log).open("w") as output:
                try:
                    run(cmd, stdout=output, stderr=subprocess.STDOUT)
                except BaseException:
                    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    raise

        for flavor in ("baseline", "current"):
            docker("mvn -B -o -s settings.xml -Dmaven.repo.local=/work/m2 -f " + flavor +
                   ".pom.xml org.apache.maven.plugins:maven-dependency-plugin:3.8.1:build-classpath -Dmdep.outputFile=/work/" + flavor + ".classpath", flavor + "-dependencies.log")
        assert (work / "baseline.classpath").read_bytes() == (work / "current.classpath").read_bytes(), "Runtime dependency drift"
        report.append("PASS: baseline/current POM migration runtime dependency classpaths are identical (offline, private cache).")
        docker('javac -cp "$(cat current.classpath)" -d classes MigrationTranslationValidation.java', "compile.log")

        def invoke(db, flavor, mode, snapshot):
            docker('java -cp "classes:' + flavor + ':$(cat ' + flavor + '.classpath)" MigrationTranslationValidation ' + db + " " + mode + " /work/" + snapshot, snapshot + ".log")
            print("Completed " + snapshot, flush=True)

        failures = []
        for db, flavor, snapshot in (("migration_baseline", "baseline", "baseline-fresh"),
                                     ("migration_current", "current", "current-fresh"),
                                     ("migration_upgrade", "baseline", "upgrade-baseline")):
            try:
                invoke(db, flavor, "update", snapshot)
            except subprocess.CalledProcessError:
                failures.append(snapshot)
        if failures:
            report.append("FAIL: unmodified master execution failed: " + ", ".join(failures) + ". See corresponding logs; no bypass or SQL modification was applied.")
            raise RuntimeError("Fresh migration failure: " + ", ".join(failures))

        def compare(a, b, suffixes):
            first = {p.name: p.read_bytes() for p in (work / a).iterdir() if p.suffix in suffixes}
            second = {p.name: p.read_bytes() for p in (work / b).iterdir() if p.suffix in suffixes}
            different = sorted(k for k in first.keys() | second.keys() if first.get(k) != second.get(k))
            assert not different, "Snapshot differences: " + ", ".join(different)
            return len(first)

        files = compare("baseline-fresh", "current-fresh", {".schema", ".stable", ".tsv"})
        report.append("PASS: fresh baseline/current schema, all seeded rows, IDs, JSON values and checksums match (%d files). Only Liquibase DATEEXECUTED/DEPLOYMENT_ID excluded; SQL clock fixed identically." % files)
        compare("baseline-fresh", "upgrade-baseline", {".schema", ".stable", ".tsv"})
        invoke("migration_upgrade", "baseline", "seed", "upgrade-before")
        invoke("migration_upgrade", "current", "update", "upgrade-after")
        compare("upgrade-before", "upgrade-after", {".schema", ".exact", ".tsv"})
        assert "PENDING_BEFORE=0" in (work / "upgrade-after.log").read_text()
        report.append("PASS: baseline-to-current update validated checksums with zero pending changes and preserved every exact row, schema and Liquibase ledger field, including synthetic edited settings/prompts.")
        invoke("migration_upgrade", "current", "update", "upgrade-repeat")
        compare("upgrade-after", "upgrade-repeat", {".schema", ".exact", ".tsv"})
        report.append("PASS: repeated current update is exactly idempotent.")
        assert before_hashes == {rel: digest((ROOT / rel).read_bytes()) for rel in paths}
        report.append("PASS: source migration bytes remained unchanged during validation.")
        report.append("\nTable row counts:\n\n```\n" + (work / "baseline-fresh/counts.tsv").read_text() + "```\n")
    except BaseException as error:
        report.append("\nValidation incomplete: " + str(error))
        raise
    finally:
        Path(args.report).write_text("\n".join(report) + "\n", encoding="ascii")
        print("Evidence: " + args.report, flush=True)
        print("Artifacts: " + str(work), flush=True)


if __name__ == "__main__":
    main()
