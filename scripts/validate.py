#!/usr/bin/env python3
"""Validate the skills repo.

Checks performed:
  1. Every SKILL.md has frontmatter with required fields, correct types,
     and no unknown fields (strict schema).
  2. `name` matches the parent folder name.
  3. `category` is in the canonical whitelist and matches the parent folder.
  4. `description` length <= 300 chars (skill-authoring rule 8; warning).
  5. Every entry in `related:` resolves to an existing skill.
  6. `related:` is bidirectional (A -> B implies B -> A).
  7. All relative markdown links inside SKILL.md / INDEX.md / README.md
     point to real files.
  8. References inside `<skill>/references/` are linked from SKILL.md and
     do not exceed the recommended quota of 1500 total lines per skill.
  9. Every tag is in tags-allowlist.txt (warning if not — add intentionally).
 10. AUTO-GENERATED marker blocks are well-formed (paired BEGIN/END, unique IDs).
 11. skills.json is up to date with the filesystem.
 12. README.md / per-category INDEX.md / .github/copilot-instructions.md
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
TAGS_ALLOWLIST_PATH = REPO_ROOT / "tags-allowlist.txt"

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
ALLOWED_FIELDS = {
    "name", "description", "category", "tags", "keywords", "related",
    # Freshness signalling for time-sensitive content (e.g. cloud SaaS skills).
    # Both fields are optional; when present we surface a warning if the skill
    # hasn't been verified within freshness_budget days. See
    # rules/cloud-content-freshness.md for the policy.
    "last_verified", "freshness_budget",
}
DESCRIPTION_MAX = 300
REFERENCES_LINES_MAX = 1500  # warn when SKILL.md + references exceed this

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MARKER_BEGIN_RE = re.compile(r"<!--\s*BEGIN AUTO-GENERATED:\s*([a-z][a-z0-9_-]*)\s*-->")
MARKER_END_RE = re.compile(r"<!--\s*END AUTO-GENERATED:\s*([a-z][a-z0-9_-]*)\s*-->")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


_FRESHNESS_BUDGET_RE = re.compile(r"^\s*(\d+)\s*d\s*$", re.IGNORECASE)


def _check_freshness(rel: Path, fm: dict) -> None:
    """If freshness fields are set, warn when last_verified is past the budget.

    Both fields are optional; if either is missing we don't enforce anything —
    only skills that opt in (typically cloud / SaaS skills) get checked.
    """
    last_verified = fm.get("last_verified")
    budget_raw = fm.get("freshness_budget")
    if last_verified is None and budget_raw is None:
        return  # opted out

    if last_verified is None:
        warn(f"{rel}: freshness_budget set but last_verified is missing")
        return
    if budget_raw is None:
        warn(f"{rel}: last_verified set but freshness_budget is missing")
        return

    # last_verified can be a date or a string YYYY-MM-DD
    import datetime as _dt
    if isinstance(last_verified, _dt.date):
        verified = last_verified
    elif isinstance(last_verified, str):
        try:
            verified = _dt.date.fromisoformat(last_verified)
        except ValueError:
            err(f"{rel}: last_verified `{last_verified}` is not a YYYY-MM-DD date")
            return
    else:
        err(f"{rel}: last_verified must be a YYYY-MM-DD date string")
        return

    if not isinstance(budget_raw, str):
        err(f"{rel}: freshness_budget must be a string like `180d`")
        return
    m = _FRESHNESS_BUDGET_RE.match(budget_raw)
    if not m:
        err(f"{rel}: freshness_budget `{budget_raw}` must look like `180d`")
        return
    budget_days = int(m.group(1))

    age = (_dt.date.today() - verified).days
    if age > budget_days:
        warn(
            f"{rel}: last_verified {verified.isoformat()} is {age} days old; "
            f"exceeds freshness_budget of {budget_days}d — re-verify drift surface"
        )


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

    # strict: reject unknown frontmatter fields so typos don't go silent
    for field in fm:
        if field not in ALLOWED_FIELDS:
            err(f"{rel}: unknown frontmatter field `{field}` (allowed: {sorted(ALLOWED_FIELDS)})")

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

    _check_freshness(rel, fm)

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
        # quota: SKILL.md + sum(references) line count
        if present:
            total = raw_body.count("\n")
            for p in ref_dir.glob("*.md"):
                if p.name.upper() == "README.MD":
                    continue
                total += p.read_text(encoding="utf-8").count("\n")
            if total > REFERENCES_LINES_MAX:
                warn(f"{skill_md.relative_to(REPO_ROOT)}: SKILL.md + references = {total} lines (recommended max {REFERENCES_LINES_MAX}; consider splitting the skill)")


def check_tags(skills: dict[str, dict]) -> None:
    """Warn on tags not in tags-allowlist.txt. The allowlist is a flat
    text file (one tag per line, lowercase, kebab-case). Add new tags
    intentionally — typos like `golang` vs `go` should be caught at PR."""
    if not TAGS_ALLOWLIST_PATH.exists():
        return  # repo without an allowlist: skip the check entirely
    allowed = {
        line.strip()
        for line in TAGS_ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    seen_unknown: dict[str, list[str]] = {}
    for name, fm in skills.items():
        for tag in fm.get("tags") or []:
            if not isinstance(tag, str):
                continue
            if tag not in allowed:
                seen_unknown.setdefault(tag, []).append(name)
    for tag, owners in sorted(seen_unknown.items()):
        owner_str = ", ".join(sorted(owners)[:3]) + (f" (+{len(owners) - 3} more)" if len(owners) > 3 else "")
        warn(f"tag `{tag}` not in tags-allowlist.txt — used by {owner_str}. Add it to the allowlist if intentional, or fix the typo.")


def check_markers() -> None:
    """Every <!-- BEGIN AUTO-GENERATED: id --> must have a matching END,
    IDs must be unique within the file, and BEGIN must precede END."""
    candidates: list[Path] = []
    candidates.append(REPO_ROOT / "README.md")
    candidates.extend(REPO_ROOT.glob("*/INDEX.md"))
    candidates.append(REPO_ROOT / "rules" / "README.md")
    candidates.append(REPO_ROOT / ".github" / "copilot-instructions.md")
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # strip fenced + inline code so prose mentions of marker syntax
        # (e.g. README explaining the convention) don't get matched
        scan_text = _FENCED_RE.sub("", text)
        scan_text = _INLINE_CODE_RE.sub("", scan_text)
        rel = path.relative_to(REPO_ROOT)
        begins = [(m.start(), m.group(1)) for m in MARKER_BEGIN_RE.finditer(scan_text)]
        ends = [(m.start(), m.group(1)) for m in MARKER_END_RE.finditer(scan_text)]
        begin_ids = [b for _, b in begins]
        end_ids = [e for _, e in ends]
        # duplicate BEGIN ids
        seen: set[str] = set()
        for bid in begin_ids:
            if bid in seen:
                err(f"{rel}: duplicate BEGIN marker id `{bid}`")
            seen.add(bid)
        # every BEGIN has matching END
        for bid in begin_ids:
            if end_ids.count(bid) == 0:
                err(f"{rel}: BEGIN marker `{bid}` has no matching END")
        # every END has matching BEGIN
        for eid in end_ids:
            if begin_ids.count(eid) == 0:
                err(f"{rel}: END marker `{eid}` has no matching BEGIN")
        # ordering: for each id, BEGIN must come before END
        for bpos, bid in begins:
            for epos, eid in ends:
                if eid == bid and epos < bpos:
                    err(f"{rel}: END marker `{bid}` appears before its BEGIN")


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
    check_tags(skills)
    check_markers()
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
