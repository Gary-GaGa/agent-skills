#!/usr/bin/env python3
"""Regenerate README.md, per-category INDEX.md, and .github/copilot-instructions.md
from skills.json.

Each managed file has a marked region between
    <!-- BEGIN AUTO-GENERATED: <id> -->
    <!-- END AUTO-GENERATED: <id> -->
that this script overwrites. Anything outside the markers is preserved.

Usage:
    python3 scripts/render_docs.py            # rewrite files
    python3 scripts/render_docs.py --check    # exit nonzero if any file is stale
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.json"


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit(f"error: {MANIFEST_PATH} missing; run scripts/build_manifest.py first")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def marker_re(block_id: str) -> re.Pattern[str]:
    return re.compile(
        rf"(<!-- BEGIN AUTO-GENERATED: {re.escape(block_id)} -->)(.*?)(<!-- END AUTO-GENERATED: {re.escape(block_id)} -->)",
        re.DOTALL,
    )


def replace_block(text: str, block_id: str, new_body: str) -> str:
    pattern = marker_re(block_id)
    if not pattern.search(text):
        raise ValueError(f"missing marker block '{block_id}'")
    replacement = f"<!-- BEGIN AUTO-GENERATED: {block_id} -->\n{new_body}\n<!-- END AUTO-GENERATED: {block_id} -->"
    return pattern.sub(lambda _: replacement, text)


# ---------- table renderers ----------


def render_categories_table(manifest: dict) -> str:
    lines = [
        "| Category | Skills | Description | Index |",
        "|----------|--------|-------------|-------|",
    ]
    for cat in manifest["categories"]:
        index_path = f"./{cat['name']}/INDEX.md"
        lines.append(
            f"| **[{cat['name']}]({index_path})** | {cat['skill_count']} | "
            f"{cat['description']} | [→ INDEX]({index_path}) |"
        )
    rules_count = len(manifest["rules"])
    lines.append(
        f"| **[rules](./rules/README.md)** | {rules_count} | "
        f"Lightweight, quotable convention sheets (Go, security, Docker, prompts, etc.). | "
        f"[→ README](./rules/README.md) |"
    )
    return "\n".join(lines)


def render_repo_summary(manifest: dict) -> str:
    totals = manifest["totals"]
    cats = len(manifest["categories"])
    return (
        f"A curated collection of **{totals['skills']} skills** and "
        f"**{totals['rules']} rule sheets** across **{cats} categories**. "
        "Each skill is a self-contained capability package that AI coding agents "
        "(Claude Code, GitHub Copilot, etc.) can load to gain domain expertise."
    )


def render_index_table(manifest: dict, category: str) -> str:
    lines = [
        "| Skill | Tags | Description |",
        "|-------|------|-------------|",
    ]
    for skill in manifest["skills"]:
        if skill["category"] != category:
            continue
        tags = ", ".join(f"`{t}`" for t in skill["tags"])
        # collapse internal whitespace for table cells; keep full description
        desc = re.sub(r"\s+", " ", skill["description"]).strip()
        lines.append(
            f"| [`{skill['name']}`](./{skill['name']}/SKILL.md) | {tags} | {desc} |"
        )
    return "\n".join(lines)


def render_index_header(manifest: dict, category: str) -> str:
    cat = next(c for c in manifest["categories"] if c["name"] == category)
    return f"## Skills ({cat['skill_count']})"


def render_copilot_skill_lists(manifest: dict) -> str:
    by_cat: dict[str, list[str]] = {c["name"]: [] for c in manifest["categories"]}
    for s in manifest["skills"]:
        by_cat[s["category"]].append(s["name"])
    rules = ", ".join(r["name"] for r in manifest["rules"])
    totals = manifest["totals"]
    cats = len(manifest["categories"])
    chunks = [f"Current skills — {totals['skills']} total across {cats} categories:"]
    for cat in manifest["categories"]:
        names = ", ".join(by_cat[cat["name"]])
        chunks.append(f"**{cat['name']} ({cat['skill_count']}):** {names}")
    chunks.append(f"Rule sheets ({totals['rules']}) in `rules/`: {rules}")
    return "\n\n".join(chunks)


def render_rules_index(manifest: dict) -> str:
    lines = [
        "| Rule | Topic |",
        "|------|-------|",
    ]
    for rule in manifest["rules"]:
        topic = rule["topic"] or "—"
        lines.append(f"| [`{rule['name']}.md`](./{rule['name']}.md) | {topic} |")
    return "\n".join(lines)


# ---------- write helpers ----------


def update_file(path: Path, transform: Callable[[str], str], check_only: bool) -> bool:
    """Returns True if the file was already up to date."""
    original = path.read_text(encoding="utf-8")
    new = transform(original)
    if original == new:
        return True
    if check_only:
        print(f"stale: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return False
    path.write_text(new, encoding="utf-8")
    print(f"wrote: {path.relative_to(REPO_ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit nonzero if any file is stale")
    args = parser.parse_args()

    manifest = load_manifest()
    all_clean = True

    # README.md
    def transform_readme(text: str) -> str:
        text = replace_block(text, "summary", render_repo_summary(manifest))
        text = replace_block(text, "categories", render_categories_table(manifest))
        return text

    all_clean &= update_file(REPO_ROOT / "README.md", transform_readme, args.check)

    # Each INDEX.md
    for cat in manifest["categories"]:
        index_path = REPO_ROOT / cat["name"] / "INDEX.md"
        if not index_path.exists():
            continue

        def make_transform(category_name: str):
            def t(text: str) -> str:
                text = replace_block(text, "header", render_index_header(manifest, category_name))
                text = replace_block(text, "skills-table", render_index_table(manifest, category_name))
                return text
            return t

        all_clean &= update_file(index_path, make_transform(cat["name"]), args.check)

    # rules/README.md
    rules_readme = REPO_ROOT / "rules" / "README.md"
    if rules_readme.exists():
        def transform_rules(text: str) -> str:
            return replace_block(text, "rules-index", render_rules_index(manifest))
        all_clean &= update_file(rules_readme, transform_rules, args.check)

    # .github/copilot-instructions.md
    copilot = REPO_ROOT / ".github" / "copilot-instructions.md"
    if copilot.exists():
        def transform_copilot(text: str) -> str:
            return replace_block(text, "skill-list", render_copilot_skill_lists(manifest))
        all_clean &= update_file(copilot, transform_copilot, args.check)

    if args.check and not all_clean:
        print("error: docs are stale; run scripts/render_docs.py", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
