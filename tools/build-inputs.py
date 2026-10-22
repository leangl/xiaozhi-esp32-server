#!/usr/bin/env python3
"""Offline image-input checks and source manifest hashes. Never reads .env/data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = {
    "python": "docker.io/library/python",
    "node": "docker.io/library/node",
    "maven": "docker.io/library/maven",
    "runtime": "docker.io/bellsoft/liberica-runtime-container",
    "mysql": "docker.io/library/mysql",
    "redis": "docker.io/library/redis",
}
SOURCES = (
    "Dockerfile-server-base", "Dockerfile-server", "Dockerfile-web", ".dockerignore",
    "main/xiaozhi-server/requirements.txt", "main/xiaozhi-server/requirements.lock", "main/manager-api/pom.xml",
    "main/manager-api/.mvn/settings.xml", "main/manager-api/.mvn/maven.config",
    "tools/service-dependency-lock.py", "tools/service-dependency-lock.java",
    "tools/service-dependency-lock-apk.sh", "tools/dependency-locks/maven-linux-aarch64.lock",
    "tools/dependency-locks/voice-deb-arm64.lock", "tools/dependency-locks/manager-apk-aarch64.lock",
    "tools/dependency-locks/maven-embedded.json",
    "main/manager-web/package.json", "main/manager-web/package-lock.json",
    "main/xiaozhi-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx",
)


def validate_image(role, value):
    repository = re.escape(REPOSITORIES[role])
    if not re.fullmatch(repository + r"(?::[A-Za-z0-9_][A-Za-z0-9_.-]*)?@sha256:[a-f0-9]{64}", value):
        # Deliberately omit the supplied string; it can contain embedded secrets.
        raise ValueError(f"{role}: require the reviewed {REPOSITORIES[role]} repository and a full sha256 digest")
    return value


def source_report(root=ROOT):
    files = []
    for name in SOURCES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Required regular source input missing: {name}")
        data = path.read_bytes()
        files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                      "bytes": len(data), "git_lfs_pointer": data.startswith(b"version https://git-lfs.github.com/spec/")})
    return {"kind": "source-input-manifest", "files": files,
            "limitations": ["Not an installed dependency SBOM or build verification",
                            "Python lock resolution targets CPython 3.10 Linux aarch64; other platforms need verification",
                            "OS/Maven archive locks target the reviewed Linux ARM64 bases and production Maven goal only",
                            "Model hash records checkout bytes, not provenance/license approval",
                            "Source hashes alone do not establish clean-build or externally observed runtime acceptance"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    images = sub.add_parser("images", help="Validate explicitly supplied reviewed image identities")
    for role in REPOSITORIES:
        images.add_argument(f"--{role}-image")
    sub.add_parser("report", help="Print source-only manifest hashes as JSON")
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            print(json.dumps(source_report(), indent=2))
        else:
            supplied = {role: getattr(args, role + "_image") for role in REPOSITORIES
                        if getattr(args, role + "_image") is not None}
            if not supplied:
                raise ValueError("Supply at least one explicit image input")
            for role, value in supplied.items():
                validate_image(role, value)
            print(f"Reviewed image syntax passed for {len(supplied)} input(s); digest existence/content was not verified")
    except (ValueError, OSError) as error:
        print(f"Build input rejected: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
