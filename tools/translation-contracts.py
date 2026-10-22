#!/usr/bin/env python3
"""Compare Python identity-bearing literals against HEAD without importing code.

This is deliberately narrower than an all-string comparison: natural-language
diagnostics and instructions may change, identifiers and matching rules may not.
"""
import ast
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
IDENTITY_FIELDS = {"name", "type", "method", "role", "tool", "tool_name", "transport",
                   "action", "state", "mode", "model", "provider", "error_code"}
MATCH_METHODS = {"get", "pop", "setdefault", "startswith", "endswith", "replace",
                 "split", "rsplit", "find", "index", "match", "search", "compile"}


def identities(source):
    result = Counter()

    def add(kind, value):
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            result[(kind, value.value)] += 1

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                add("dict-key", key)
                if isinstance(key, ast.Constant) and key.value in IDENTITY_FIELDS:
                    add("identity:" + key.value, value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in MATCH_METHODS and node.args:
                add("call:" + node.func.attr, node.args[0])
        elif isinstance(node, ast.Compare):
            for value in [node.left, *node.comparators]:
                add("comparison", value)
        elif isinstance(node, ast.Subscript):
            add("subscript", node.slice)
    return result


def main():
    paths = subprocess.check_output(["git", "diff", "--name-only", "-z", "HEAD"], cwd=ROOT).decode().split("\0")
    failures, checked = [], 0
    for rel in filter(lambda p: p.endswith(".py"), paths):
        file = ROOT / rel
        if not file.is_file():
            continue
        before = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT).decode("utf-8-sig")
        old, new = identities(before), identities(file.read_text(encoding="utf-8-sig"))
        checked += 1
        if old != new:
            # Values may be credentials or user data: report counts/categories,
            # never print literal content automatically.
            failures.append({"path": rel, "removed": sum((old-new).values()),
                             "added": sum((new-old).values()),
                             "categories": sorted({kind for kind, _ in (old-new).keys() | (new-old).keys()})})
    print(json.dumps({"checkedPythonFiles": checked, "failures": failures}, indent=2))
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
