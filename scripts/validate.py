#!/usr/bin/env python3
"""Validate the skills repo.

Checks performed:
  1. Every SKILL.md has frontmatter with required fields
     (name, description, category, tags).
  2. `name` matches the parent folder name.
  3. `category` is in the canonical whitelist and matches the parent folder.
  4. `description` length <= 300 chars (skill-authoring rule 8).
  5. Every entry in `related:` resolves to an existing skill.
  6. `related:` is bidirectional (A -> B implies B -> A).
  7. All relative markdown links inside SKILL.md / INDEX.md / README.md
     point to real files.
  8. skills.json is up to date with the filesystem.
  9. README.md / per-category INDEX.md / .github/copilot-instructions.md
     are up to date with skills.json.

Usage:
    python3 scripts/validate.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_CATEGORIES = {
    "ai-engineering",
    "engineering",
    "devops",
    "data",
    "content",
    "finance",
    "productivity",
}
REQUIRED_FIELDS = ("name", "description", "category", "tags")
DESCRIPTION_MAX = 300

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        err(f"{path.relative_to(REPO_ROOT)}: missing frontmatter")
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        err(f"{path.relative_to(REPO_ROOT)}: YAML parse error: {e}")
        return None
    if not isinstance(data, dict):
        err(f"{path.relative_to(REPO_ROOT)}: frontmatter is not a mapping")
        return None
    return data


def check_skill(path: Path) -> dict | None:
    rel = path.relative_to(REPO_ROOT)
    fm = parse_frontmatter(path)
    if fm is None:
        return None

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] in (None, "", []):
            err(f"{rel}: missing required frontmatter field `{field}`")

    name = fm.get("name", "")
    folder_name = path.parent.name
    if name != folder_name:
        err(f"{rel}: name `{name}` does not match folder `{folder_name}`")

    category = fm.get("category", "")
    parent_category = path.parent.parent.name
    if category not in VALID_CATEGORIES:
        err(f"{rel}: category `{category}` is not in whitelist {sorted(VALID_CATEGORIES)}")
    if category and category != parent_category:
        err(f"{rel}: category `{category}` does not match parent folder `{parent_category}`")

    description = (fm.get("description") or "").strip()
    if description and len(description) > DESCRIPTION_MAX:
        # skill-authoring rule 8 is a soft guideline; surface as warning
        warn(f"{rel}: description is {len(description)} chars (recommended max {DESCRIPTION_MAX})")

    if not isinstance(fm.get("tags") or [], list):
        err(f"{rel}: tags must be a list")
    if not isinstance(fm.get("related") or [], list):
        err(f"{rel}: related must be a list")

    if "keywords" in fm:
        kw = fm["keywords"]
        if not isinstance(kw, list):
            err(f"{rel}: keywords must be a list")
        else:
            seen: set[str] = set()
            for item in kw:
                if not isinstance(item, str) or not item.strip():
                    err(f"{rel}: keywords entries must be non-empty strings")
                    continue
                norm = item.strip().lower()
                if norm in seen:
                    err(f"{rel}: duplicate keyword `{item}`")
                seen.add(norm)
            if len(kw) > 20:
                warn(f"{rel}: {len(kw)} keywords (recommended max 20; keep BM25-focused)")
            tag_set = {t.lower() for t in (fm.get("tags") or []) if isinstance(t, str)}
            kw_set = {item.strip().lower() for item in kw if isinstance(item, str)}
            if tag_set and kw_set and kw_set <= tag_set:
                warn(f"{rel}: keywords is a subset of tags — add proper nouns / acronyms / error codes that differ from tags")

    return fm


def collect_all_skills() -> dict[str, dict]:
    """Return {skill_name: frontmatter_dict_with_path}."""
    result: dict[str, dict] = {}
    for skill_md in sorted(REPO_ROOT.glob("*/*/SKILL.md")):
        if "scripts" in skill_md.parts:
            continue
        fm = check_skill(skill_md)
        if fm is None:
            continue
        name = fm.get("name", "")
        if name in result:
            err(f"duplicate skill name `{name}` at {skill_md.relative_to(REPO_ROOT)}")
            continue
        fm["_path"] = skill_md
        result[name] = fm
    return result


_FENCED_RE = re.compile(r"```.*?```", re.DOTALL)


def _strip_code(text: str) -> str:
    """Remove fenced code blocks so prose-pattern matchers don't trip on
    illustrative paths inside ``` blocks (directory trees, example bodies).
    Inline `code` is intentionally preserved — repos like copilot-sdk wrap
    real reference filenames in backticks."""
    return _FENCED_RE.sub("", text)


def check_references(skills: dict[str, dict]) -> None:
    """For every skill with a references/ folder:
       (a) every *.md inside is referenced from SKILL.md body,
       (b) every references/ link in SKILL.md points to an existing file."""
    for fm in skills.values():
        skill_md: Path = fm["_path"]
        ref_dir = skill_md.parent / "references"
        raw_body = skill_md.read_text(encoding="utf-8")
        prose_body = _strip_code(raw_body)
        # files actually present
        present: set[str] = set()
        if ref_dir.is_dir():
            for p in ref_dir.glob("*.md"):
                if p.name.upper() == "README.MD":
                    continue
                present.add(p.name)
        # files mentioned in body — accept Markdown links (raw, so backtick
        # labels survive) and plain prose mentions outside of code blocks.
        mentioned: set[str] = set()
        for _, target in LINK_RE.findall(raw_body):
            target = target.strip()
            if target.startswith("./references/") or target.startswith("references/"):
                fname = Path(target).name.split("#", 1)[0].split("?", 1)[0]
                if fname:
                    mentioned.add(fname)
        for m in re.finditer(r"(?<![\w/])references/([\w.\-]+\.md)", prose_body):
            mentioned.add(m.group(1))
        # orphans: files present but not mentioned
        for fname in sorted(present - mentioned):
            rel = (ref_dir / fname).relative_to(REPO_ROOT)
            err(f"{rel}: orphan reference — not linked from {skill_md.relative_to(REPO_ROOT)}")
        # dangling: mentioned but missing on disk
        for fname in sorted(mentioned - present):
            err(f"{skill_md.relative_to(REPO_ROOT)}: references `references/{fname}` but file does not exist")


def check_related(skills: dict[str, dict]) -> None:
    for name, fm in skills.items():
        for ref in fm.get("related") or []:
            if ref == name:
                err(f"{name}: lists itself in `related`")
                continue
            if ref not in skills:
                err(f"{name}: related skill `{ref}` does not exist")
                continue
            back = skills[ref].get("related") or []
            if name not in back:
                err(f"`related` not bidirectional: {name} -> {ref}, but {ref} does not list {name}")


def check_links(skills: dict[str, dict]) -> None:
    files: list[Path] = []
    files.extend(REPO_ROOT.glob("*/*/SKILL.md"))
    files.extend(REPO_ROOT.glob("*/*/references/*.md"))
    files.extend(REPO_ROOT.glob("*/INDEX.md"))
    files.append(REPO_ROOT / "README.md")
    files.append(REPO_ROOT / "CONTRIBUTING.md")
    # SKILL_TEMPLATE.md intentionally excluded — it contains placeholder
    # paths like `../other-skill/SKILL.md` that are not meant to resolve.
    rules_readme = REPO_ROOT / "rules" / "README.md"
    if rules_readme.exists():
        files.append(rules_readme)
    evals_readme = REPO_ROOT / "evals" / "README.md"
    if evals_readme.exists():
        files.append(evals_readme)

    for f in files:
        if not f.exists():
            continue
        rel = f.relative_to(REPO_ROOT)
        text = f.read_text(encoding="utf-8")
        for label, target in LINK_RE.findall(text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # strip URL fragment / query
            target_path = target.split("#", 1)[0].split("?", 1)[0]
            if not target_path:
                continue
            resolved = (f.parent / target_path).resolve()
            if not resolved.exists():
                err(f"{rel}: broken link `{target}` -> {resolved.relative_to(REPO_ROOT) if REPO_ROOT in resolved.parents else resolved}")


def run_subscript(args: list[str], description: str) -> bool:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err(f"{description} failed:\n{proc.stdout}{proc.stderr}".rstrip())
        return False
    return True


def main() -> int:
    skills = collect_all_skills()
    check_related(skills)
    check_references(skills)
    check_links(skills)

    # Drift checks
    run_subscript(["scripts/build_manifest.py", "--check"], "skills.json drift check")
    run_subscript(["scripts/render_docs.py", "--check"], "docs drift check")

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"ok: {len(skills)} skills validated, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
