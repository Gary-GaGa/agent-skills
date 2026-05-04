#!/usr/bin/env python3
"""Build skills.json from SKILL.md frontmatter and rules/.

Single source of truth for the skill index. README.md, per-category
INDEX.md, and .github/copilot-instructions.md are regenerated from the
manifest by render_docs.py.

Usage:
    python3 scripts/build_manifest.py            # write skills.json
    python3 scripts/build_manifest.py --check    # exit nonzero if drift
    python3 scripts/build_manifest.py --stdout   # print without writing
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.json"
SCHEMA_VERSION = 1

# Category metadata. Order here is the canonical display order.
CATEGORIES: list[dict[str, str]] = [
    {
        "name": "engineering",
        "title": "Engineering",
        "description": "Software design, Go, APIs, frontend, databases, architecture, integrations.",
    },
    {
        "name": "ai-engineering",
        "title": "AI Engineering",
        "description": "LLM agents, prompts, context, tools, eval, observability, safety, caching.",
    },
    {
        "name": "devops",
        "title": "DevOps",
        "description": "Docker, GitHub Actions, Terraform, Kubernetes.",
    },
    {
        "name": "data",
        "title": "Data",
        "description": "SQL, database migrations, data modeling.",
    },
    {
        "name": "content",
        "title": "Content",
        "description": "Medium writing, technical docs, newsletters.",
    },
    {
        "name": "finance",
        "title": "Finance",
        "description": "Taiwan stock analysis, ETF, options, portfolio, tax.",
    },
    {
        "name": "productivity",
        "title": "Productivity",
        "description": "Learning methodology, second brain, time management.",
    },
]
VALID_CATEGORIES: set[str] = {c["name"] for c in CATEGORIES}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], int]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    body = text[match.end():]
    body_lines = body.count("\n")
    return data, body_lines


def collect_skills() -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    for category in CATEGORIES:
        cat_dir = REPO_ROOT / category["name"]
        if not cat_dir.is_dir():
            continue
        for skill_dir in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            fm, body_lines = parse_frontmatter(skill_md)
            skills.append(
                {
                    "name": fm.get("name", ""),
                    "category": fm.get("category", ""),
                    "description": (fm.get("description") or "").strip(),
                    "tags": list(fm.get("tags") or []),
                    "keywords": list(fm.get("keywords") or []),
                    "related": list(fm.get("related") or []),
                    "path": str(skill_md.relative_to(REPO_ROOT)),
                    "body_lines": body_lines,
                }
            )
    skills.sort(key=lambda s: (s["category"], s["name"]))
    return skills


RULE_ROW_RE = re.compile(r"^\|\s*\[`([^`]+)`\]\(\./([^)]+)\)\s*\|\s*(.+?)\s*\|\s*$")


def collect_rules() -> list[dict[str, Any]]:
    rules_dir = REPO_ROOT / "rules"
    readme = rules_dir / "README.md"
    topics: dict[str, str] = {}
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            m = RULE_ROW_RE.match(line)
            if m:
                topics[m.group(2)] = m.group(3).strip()
    rules: list[dict[str, Any]] = []
    for path in sorted(rules_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        rules.append(
            {
                "name": path.stem,
                "path": str(path.relative_to(REPO_ROOT)),
                "topic": topics.get(path.name, ""),
            }
        )
    return rules


def category_counts(skills: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {c["name"]: 0 for c in CATEGORIES}
    for s in skills:
        counts[s["category"]] = counts.get(s["category"], 0) + 1
    return counts


def build_manifest() -> dict[str, Any]:
    skills = collect_skills()
    rules = collect_rules()
    counts = category_counts(skills)
    categories = [
        {**c, "skill_count": counts.get(c["name"], 0)} for c in CATEGORIES
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "categories": categories,
        "skills": skills,
        "rules": rules,
        "totals": {
            "skills": len(skills),
            "rules": len(rules),
            "categories": len(categories),
        },
    }


def serialize(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit nonzero if skills.json is stale")
    parser.add_argument("--stdout", action="store_true", help="print to stdout instead of writing")
    args = parser.parse_args()

    manifest = build_manifest()
    payload = serialize(manifest)

    if args.stdout:
        sys.stdout.write(payload)
        return 0

    if args.check:
        if not MANIFEST_PATH.exists():
            print(f"error: {MANIFEST_PATH} does not exist; run build_manifest.py", file=sys.stderr)
            return 1
        existing = MANIFEST_PATH.read_text(encoding="utf-8")
        if existing != payload:
            print(f"error: {MANIFEST_PATH} is stale; run scripts/build_manifest.py", file=sys.stderr)
            return 1
        print(f"ok: {MANIFEST_PATH} is up to date")
        return 0

    MANIFEST_PATH.write_text(payload, encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({manifest['totals']['skills']} skills, {manifest['totals']['rules']} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
