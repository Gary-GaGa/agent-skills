#!/usr/bin/env python3
"""Auto-fix bidirectional `related:` references.

For every A -> B where B does not list A, append A to B's `related:` list.
Edits the `related: [...]` line in-place; relies on every skill using the
single-line list form (verified by validate.py separately).

Run after adding or removing skills, then commit the changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTMATTER_RE = re.compile(r"\A(---\n)(.*?)(\n---\n)", re.DOTALL)
RELATED_LINE_RE = re.compile(r"^related:\s*\[(.*?)\]\s*$", re.MULTILINE)


def collect() -> dict[str, dict]:
    skills: dict[str, dict] = {}
    for path in sorted(REPO_ROOT.glob("*/*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        fm = yaml.safe_load(m.group(2)) or {}
        name = fm.get("name") or path.parent.name
        skills[name] = {
            "path": path,
            "related": list(fm.get("related") or []),
        }
    return skills


def add_related(path: Path, additions: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    m = RELATED_LINE_RE.search(text)
    if not m:
        sys.exit(f"{path}: no single-line `related: [...]` to patch (manual fix required)")
    inside = m.group(1).strip()
    current = [x.strip() for x in inside.split(",") if x.strip()] if inside else []
    seen = set(current)
    for a in additions:
        if a not in seen:
            current.append(a)
            seen.add(a)
    new_line = f"related: [{', '.join(current)}]"
    new_text = text[: m.start()] + new_line + text[m.end():]
    path.write_text(new_text, encoding="utf-8")


def main() -> int:
    skills = collect()
    pending: dict[str, list[str]] = {name: [] for name in skills}
    for name, info in skills.items():
        for ref in info["related"]:
            if ref == name or ref not in skills:
                continue
            if name not in skills[ref]["related"]:
                pending[ref].append(name)
    pending = {k: sorted(set(v)) for k, v in pending.items() if v}
    if not pending:
        print("ok: all related references are already bidirectional")
        return 0
    for target, additions in sorted(pending.items()):
        path = skills[target]["path"]
        add_related(path, additions)
        rel = path.relative_to(REPO_ROOT)
        print(f"{rel}: appended {additions}")
    print(f"\npatched {len(pending)} file(s); re-run scripts/validate.py to confirm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
