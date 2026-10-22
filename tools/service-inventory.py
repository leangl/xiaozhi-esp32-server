#!/usr/bin/env python3
"""Static source inventory only: output hosts/imports/setting names, never keys or payloads.

This finds review candidates; it does not classify corporate ownership, prove
actual egress, or approve an endpoint from its suffix. Ignored/local config and
running application data are deliberately not read.
"""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
PREFIXES = ("main/xiaozhi-server/core/", "main/xiaozhi-server/config/",
            "main/xiaozhi-server/plugins_func/", "main/manager-api/src/main/java/",
            "main/manager-api/.mvn/", ".github/workflows/")
SPECIAL = {"Dockerfile-server", "Dockerfile-server-base", "Dockerfile-web", "docker-setup.sh",
           "main/xiaozhi-server/config.yaml", "main/xiaozhi-server/config_from_api.yaml",
           "main/xiaozhi-server/docker-compose.yml", "main/xiaozhi-server/docker-compose_all.yml",
           "main/xiaozhi-server/requirements.txt", "main/manager-api/pom.xml"}
URL = re.compile(r"(?:https?|wss?)://[^\s\"'<>]+")
SETTING = re.compile(r"\b(?:base_url|api_url|api_host|endpoint|mcp_endpoint|proxy|proxies|url)\b")
SDK = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.M)
NETWORK = re.compile(r"requests\.|httpx\.|aiohttp\.|urlopen|RestTemplate|HttpRequest|HttpClient|"
                     r"new\s+(?:URL|URI)|subprocess\.|from_pretrained|snapshot_download|"
                     r"torch\.hub|allow_redirects|follow_redirects|trust_env")


def inventory():
    paths = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others",
                                     "--exclude-standard"], cwd=ROOT).decode().split("\0")
    result = []
    for relative in sorted(set(paths)):
        if not relative or not (relative.startswith(PREFIXES) or relative in SPECIAL):
            continue
        path = ROOT / relative
        if not path.is_file() or path.suffix.lower() in {".wav", ".mp3", ".png", ".onnx", ".pyc"}:
            continue
        raw = path.read_bytes()
        try:
            source = raw.decode("utf-8")
        except UnicodeError:
            continue
        imports = set()
        if path.suffix == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.add(node.module)
            except SyntaxError:
                imports.update(SDK.findall(source))
        elif path.suffix == ".java":
            imports.update(re.findall(r"^import\s+([\w.]+)", source, re.M))
        hosts = []
        fields = []
        calls = []
        templates = []
        for line, text in enumerate(source.splitlines(), 1):
            for candidate in URL.findall(text):
                try:
                    host = urlsplit(candidate).hostname
                except ValueError:
                    host = None
                if host and re.fullmatch(r"[A-Za-z0-9.:-]+", host):
                    hosts.append({"host": host.lower().rstrip("."), "line": line})
                else:
                    templates.append(line)
            if SETTING.search(text):
                fields.append(line)
            if NETWORK.search(text):
                calls.append(line)
        provider = relative.startswith("main/xiaozhi-server/core/providers/") and path.suffix == ".py"
        if provider or hosts or fields or calls or relative in SPECIAL:
            result.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                           "imports": sorted(imports), "literalHosts": hosts,
                           "dynamicUrlLines": sorted(set(templates)), "endpointSettingLines": fields,
                           "networkOrDownloadLines": calls, "review": "pending"})
    return {"schemaVersion": 1, "date": "2026-10-20", "scope": "source-only-backend-candidates",
            "baselineCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "warning": "Review inventory, not an allowlist or externally observed traffic report",
            "files": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate the mechanical source inventory")
    args = parser.parse_args()
    data = inventory()
    encoded = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    if args.write:
        target = ROOT / "docs/maintenance/service-inventory.json"
        target.write_text(encoded, encoding="ascii")
        print(json.dumps({"files": len(data["files"]), "output": str(target)}))
    else:
        print(encoded, end="")
