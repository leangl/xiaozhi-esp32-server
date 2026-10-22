#!/usr/bin/env python3
"""Export only public source inputs for disposable verification, never operator profiles."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def export_source(destination):
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    count = 0
    for name in paths:
        path = Path(name)
        if not name or not name.startswith(("main/manager-api/", "main/manager-web/", "main/xiaozhi-server/")):
            continue
        if any(part in {"data", "tmp", "node_modules", "target", "dist", "coverage", "__pycache__"} for part in path.parts):
            continue
        if path.name.startswith((".env", ".config", ".npmrc", "application-")):
            continue
        source = ROOT / path
        if not source.is_file() or source.is_symlink():
            continue
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    destination = args.output or Path(tempfile.mkdtemp(prefix="xiaozhi-policy-public-source-", dir="/private/tmp"))
    if args.output:
        destination.mkdir(exist_ok=False, parents=True)
    count = export_source(destination)
    print(json.dumps({"public_source": str(destination), "files": count,
                      "excluded": ["operator profiles", "env/config/data", "generated dependencies/builds"]}))


if __name__ == "__main__":
    main()
