#!/usr/bin/env python3
"""Read-only structural checks for the English translation, against HEAD.

String/docstring changes still require semantic review. This does not prove
protocol compatibility or replace runtime tests.
"""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class WithoutProse(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = "<text>"
        return node

    def visit_JoinedStr(self, node):
        # Translations may move prose before/after an interpolation. Preserve
        # interpolation order/expressions, not literal-text fragment positions.
        node.values = [self.visit(v) for v in node.values if isinstance(v, ast.FormattedValue)]
        return node

    def visit_FormattedValue(self, node):
        node.value = self.visit(node.value)
        # Format specs are executable formatting instructions, not prose.
        return node


def signature(source):
    tree = ast.parse(source)
    # Docstrings can be added to explain retained language fixtures.
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                body.pop(0)
    return ast.dump(WithoutProse().visit(tree), include_attributes=False)


def main():
    failures, notes = [], []
    paths = git("diff", "--name-only", "-z", "HEAD").decode().split("\0")
    counts = {"pythonSyntax": 0, "pythonStructure": 0, "xmlStructure": 0,
              "digitalHumanCss": 0, "jsonShape": 0}
    for rel in filter(None, paths):
        file = ROOT / rel
        if not file.is_file():
            continue
        try:
            old = git("show", f"HEAD:{rel}").decode("utf-8-sig")
            new = file.read_text(encoding="utf-8-sig")
        except (UnicodeError, subprocess.CalledProcessError):
            continue
        try:
            if file.suffix == ".py":
                compile(new, rel, "exec")
                counts["pythonSyntax"] += 1
                if signature(old) != signature(new):
                    failures.append({"path": rel, "error": "Non-prose Python AST changed"})
                else:
                    counts["pythonStructure"] += 1
            elif rel.startswith("main/manager-api/src/main/resources/") and file.suffix == ".xml":
                # Strip comments only; all elements, attributes and text must match.
                normalize = lambda s: "\n".join(line.rstrip() for line in s.splitlines()).strip()
                remove_comments = lambda s: normalize(re.sub(r"<!--.*?-->", "", s, flags=re.S))
                ET.fromstring(new)
                if remove_comments(old) != remove_comments(new):
                    failures.append({"path": rel, "error": "XML changed outside comments"})
                else:
                    counts["xmlStructure"] += 1
            elif rel == "main/digital-human/css/index.css":
                strip = lambda s: re.sub(r"/\*.*?\*/", "", s, flags=re.S).strip()
                if strip(old) != strip(new):
                    failures.append({"path": rel, "error": "CSS changed outside comments"})
                else:
                    counts["digitalHumanCss"] += 1
            elif file.suffix == ".json":
                def shape(value):
                    if isinstance(value, dict):
                        return {k: shape(v) for k, v in value.items()}
                    if isinstance(value, list):
                        return [shape(v) for v in value]
                    return "<text>" if isinstance(value, str) else value
                try:
                    before, after = json.loads(old), json.loads(new)
                except json.JSONDecodeError:
                    notes.append({"path": rel, "note": "Not strict JSON; use module tooling"})
                    continue
                if shape(before) != shape(after):
                    failures.append({"path": rel, "error": "JSON keys/non-text values changed"})
                else:
                    counts["jsonShape"] += 1
        except (SyntaxError, ET.ParseError) as error:
            failures.append({"path": rel, "error": str(error)})
    print(json.dumps({"checked": counts, "failures": failures, "notes": notes}, indent=2))
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
