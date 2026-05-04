#!/usr/bin/env python3
"""Suggest (and optionally apply) bidirectional `related:` back-references.

For every A -> B where B does not list A, the script reports it and, with
`--apply`, appends A to B's `related:` list. Default is dry-run so a
maintainer can review the diff before committing — auto-mutation can add
back-references the original author intentionally omitted.

Edits the `related: [...]` line in-place; relies on every skill using the
single-line list form (verified by validate.py separately).

Usage:
    python3 scripts/fix_related.py            # dry-run, prints what would change
    python3 scripts/fix_related.py --apply    # actually edit the SKILL.md files
"""
from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually edit SKILL.md files; default is dry-run (advisory only)",
    )
    args = parser.parse_args()

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

    mode = "would append" if not args.apply else "appended"
    for target, additions in sorted(pending.items()):
        path = skills[target]["path"]
        rel = path.relative_to(REPO_ROOT)
        if args.apply:
            add_related(path, additions)
        print(f"{rel}: {mode} {additions}")

    if args.apply:
        print(f"\npatched {len(pending)} file(s); re-run scripts/validate.py to confirm")
    else:
        print(
            f"\n{len(pending)} file(s) would be patched. Re-run with --apply to edit, "
            "or update the source SKILL.md files manually if some back-references "
            "were intentionally omitted."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
