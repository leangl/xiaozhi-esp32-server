#!/usr/bin/env python3
"""Run the production service-policy upgrade on disposable, synthetic MySQL only.

Creates a labeled internal network and tmpfs database, no published ports and no
existing data/config mounts. Source and dependency cache are mounted read-only.
Offline Maven compilation is not a clean-cache supply-chain build certificate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
LABEL = "xiaozhi.validation=service-policy-migration-20261021"
MAVEN = "docker.io/library/maven:3.9.11-eclipse-temurin-21@sha256:6fdc855a6ed81d288ca7ca37ac6ff5e9308b612485c0801d70b25a858c83d237"
MYSQL = "docker.io/library/mysql:8.4@sha256:0f51e63e537a1f176423fa03ef559aabe6fa4372a53160a44bc7e75da7d15364"


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", default="/private/tmp/xiaozhi-translation-m2")
    parser.add_argument("--settings", default="/private/tmp/xiaozhi-maven-test-settings.xml")
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix="xiaozhi-policy-migration-", dir="/private/tmp"))
    spec = importlib.util.spec_from_file_location("public_source", ROOT / "tools/service-source-snapshot.py")
    public_source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(public_source)
    public_source.export_source(work / "public-source")
    name = work.name
    database = name + "-db"
    runner = name + "-runner"
    report = ["# Service-policy migration rehearsal", "", "Synthetic fixtures only; no existing deployment/data accessed.",
              "No host ports; internal Docker network; no AI/SMS calls.", "Artifacts: " + str(work), ""]
    protected = json.loads((ROOT / "docs/maintenance/english-baseline.json").read_text())["protectedHashes"]
    for rel, expected in protected.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
    try:
        run(["docker", "network", "create", "--internal", "--label", LABEL, name], stdout=subprocess.DEVNULL)
        run(["docker", "run", "-d", "--rm", "--name", database, "--label", LABEL,
             "--network", name, "--network-alias", "policy-db", "--read-only",
             "--tmpfs", "/var/lib/mysql", "--tmpfs", "/var/run/mysqld", "--tmpfs", "/tmp",
             "-e", "MYSQL_ROOT_PASSWORD=disposable-validation-only", MYSQL], stdout=subprocess.DEVNULL)
        for attempt in range(90):
            ready = subprocess.run(["docker", "exec", "-e", "MYSQL_PWD=disposable-validation-only", database,
                                    "mysql", "-uroot", "-Nse", "SELECT 1"], capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Disposable database did not become ready")
        run(["docker", "exec", "-e", "MYSQL_PWD=disposable-validation-only", database,
             "mysql", "-uroot", "-e", "CREATE DATABASE policy_fresh; CREATE DATABASE policy_upgrade;"], stdout=subprocess.DEVNULL)
        shutil.copy2(ROOT / "tools/service-migration-validation.java", work / "ServiceMigrationValidation.java")
        command = (
            "cp -a /source /tmp/project && cd /tmp/project && "
            "mvn -o -B -ntp -s /settings.xml -Dmaven.repo.local=/cache -DskipTests compile "
            "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:build-classpath -Dmdep.outputFile=/work/classpath && "
            'javac -cp "target/classes:$(cat /work/classpath)" -d /work/classes /work/ServiceMigrationValidation.java && '
            'java -cp "/work/classes:target/classes:$(cat /work/classpath)" ServiceMigrationValidation policy_fresh && '
            'java -cp "/work/classes:target/classes:$(cat /work/classpath)" ServiceMigrationValidation policy_upgrade'
        )
        with (work / "validation.log").open("w") as output:
            run(["docker", "run", "--rm", "--name", runner, "--label", LABEL, "--network", name,
                 "--read-only", "--tmpfs", "/tmp", "-v", str(work / "public-source/main/manager-api") + ":/source:ro",
                 "-v", str(Path(args.cache).resolve()) + ":/cache:ro",
                 "-v", str(Path(args.settings).resolve()) + ":/settings.xml:ro",
                 "-v", str(work) + ":/work", "--entrypoint", "/bin/sh", MAVEN, "-ec", command],
                stdout=output, stderr=subprocess.STDOUT)
        passes = [line for line in (work / "validation.log").read_text().splitlines() if line.startswith("PASS ")]
        assert len(passes) == 2, "Incomplete scenario markers"
        report.extend(passes)
        report.append("PASS: %d historical SQL/locale hashes unchanged." % len(protected))
        print("\n".join(passes), flush=True)
    except BaseException as error:
        report.append("INCOMPLETE: " + type(error).__name__ + "; inspect synthetic validation.log")
        raise
    finally:
        for container in (runner, database):
            subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "network", "rm", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (work / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("Evidence: " + str(work / "report.md"), flush=True)


if __name__ == "__main__":
    main()
