#!/usr/bin/env python3
"""Reject known retired SDKs, active destinations and build mirrors in source.

This bounded reintroduction gate is not runtime egress proof or an ownership
classifier. Approved destination checks remain in the actual outbound clients.
Historical resources are exempt only by original exact SHA-256. Tests and factual
documentation are not executable presets and are deliberately not scanned.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
RETIRED_IMPORTS = frozenset({"dashscope", "aip", "cozepy", "funasr", "modelscope",
                             "powermem", "mem0", "edge_tts", "volcengine", "zhipuai"})
RETIRED_PACKAGES = frozenset({"dashscope", "baidu-aip", "cozepy", "funasr", "modelscope",
                              "powermem", "mem0ai", "edge-tts", "volcengine", "zhipuai", "mcp-proxy"})
RETIRED_HOSTS = re.compile(
    r"(?:https?://|wss?://)(?:[^/\s\"'@]*@)?(?:[a-z0-9-]+\.)*(?:"
    r"aliyun(?:cs)?\.com|aliyuncs\.com|alibabacloud\.com|baidu\.com|bcebos\.com|"
    r"tencent(?:cloud)?\.com|myqcloud\.com|volces\.com|volcengine\.com|coze\.(?:cn|com)|"
    r"xfyun\.cn|bigmodel\.cn|deepseek\.com|siliconflow\.(?:cn|com)|minimax\.(?:chat|io)|"
    r"302\.ai|fish\.audio|modelscope\.cn|qweather\.com|hefeng\.com|metaso\.cn|"
    r"chinanews\.com(?:\.cn)?|newsnow\.busiyi\.world|pconline\.com\.cn|"
    r"npmmirror\.com|jsdelivr\.net|ghproxy\.com|docker\.[a-z0-9.-]*1ms\.run)(?=[:/\s\"']|$)", re.I)


def findings(path, content):
    result = []
    if path.endswith(".py"):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return [(1, "unparseable-python")]
        for node in ast.walk(tree):
            names = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            if any(name.split(".")[0] in RETIRED_IMPORTS for name in names):
                result.append((node.lineno, "retired-sdk-import"))
    for line, text in enumerate(content.splitlines(), 1):
        if RETIRED_HOSTS.search(text):
            result.append((line, "retired-service-or-mirror"))
        if Path(path).name.startswith("requirements"):
            if not text.lstrip().startswith("#") and re.search(r"(?:https?://|git\+|--(?:index|extra-index|find-links))", text):
                result.append((line, "unreviewed-dependency-source"))
            package = re.split(r"[=<>!~;\[\s]", text.strip())[0].lower().replace("_", "-")
            if package in RETIRED_PACKAGES:
                result.append((line, "retired-sdk-dependency"))
    return result


def in_scope(path):
    if "/tests/" in path or "/src/test/" in path or path.endswith(".test.mjs"):
        return False
    return ((path.startswith("main/xiaozhi-server/") and Path(path).suffix in {".py", ".yaml", ".yml", ".json", ".txt", ".lock"}
             and "/performance_tester/" not in path and "/models/" not in path)
            or (path.startswith("main/manager-api/src/main/") and Path(path).suffix in {".java", ".xml", ".yml", ".yaml", ".sql"})
            or path == "main/manager-api/pom.xml" or path.startswith("main/manager-api/.mvn/")
            or path.startswith("Dockerfile") or path.startswith(".github/workflows/")
            or Path(path).name.startswith(("docker-compose", "docker-setup")))


def self_test():
    assert findings("main/xiaozhi-server/core/fixture.py", "import dashscope\n")
    assert findings("main/xiaozhi-server/requirements.txt", "modelscope==1.0\n")
    assert findings("main/xiaozhi-server/requirements.lock", "package @ https://unknown.example/file.whl\n")
    assert findings("main/xiaozhi-server/config.yaml", "base_url: https://api.deepseek.com/v1\n")
    assert findings("Dockerfile-test", "RUN pip install -i https://mirrors.aliyun.com/pypi/simple test\n")
    assert not findings("main/xiaozhi-server/config.yaml", "base_url: http://127.0.0.1:9000/v1\n")
    assert not findings("main/xiaozhi-server/core/fixture.py", "from config.service_policy import validate_endpoint\n")
    print("PASS: deliberately reintroduced SDK, endpoint and mirror fixtures are rejected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    protected = json.loads((ROOT / "docs/maintenance/english-baseline.json").read_text())["protectedHashes"]
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    failures = []
    count = 0
    for path in paths:
        file = ROOT / path
        if not path or not file.is_file() or not in_scope(path):
            continue
        raw = file.read_bytes()
        if path in protected:
            if hashlib.sha256(raw).hexdigest() != protected[path]:
                failures.append({"path": path, "line": 1, "rule": "immutable-history-changed"})
            continue
        count += 1
        failures.extend({"path": path, "line": line, "rule": rule}
                        for line, rule in findings(path, raw.decode("utf-8")))
    print(json.dumps({"checked": count, "failures": failures}, indent=2))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
