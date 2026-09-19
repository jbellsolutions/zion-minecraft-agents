#!/usr/bin/env python3
"""Install repository skills into one explicit Hermes home without replacing learned skills."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

SKILLS = ("zion", "hermes-minecraft-superbuilder", "forge-1214-assets")


def tree_hash(path):
    digest = hashlib.sha256()
    for item in sorted(Path(path).rglob("*")):
        if item.is_symlink():
            raise ValueError("Symlinks are not allowed in managed skill directories")
        if item.is_file():
            digest.update(str(item.relative_to(path)).encode())
            digest.update(b"\0")
            digest.update(item.read_bytes())
    return digest.hexdigest()


def install(repo, hermes_home):
    repo = Path(repo).resolve()
    hermes_home = Path(hermes_home).expanduser().absolute()
    if not hermes_home.is_dir():
        raise ValueError("The selected Hermes home must already exist")
    destination = hermes_home / "skills" / "zion-supercharge"
    if any(p.is_symlink() for p in [destination, *destination.parents]):
        raise ValueError("Hermes destination cannot traverse symlinks")
    receipt = destination / "installation.json"
    prior = json.loads(receipt.read_text()) if receipt.exists() else {}
    for skill in (hermes_home / "skills").rglob("SKILL.md"):
        if destination in skill.parents:
            continue
        if skill.is_symlink():
            continue
        text = skill.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1] if text.startswith("---") else ""
        match = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", frontmatter, re.M)
        if match and match.group(1) in SKILLS:
            raise ValueError("An existing skill uses the same command name; preserve and merge it first: " + str(skill))
    for name in SKILLS:
        if not (repo / "skills" / name / "SKILL.md").is_file():
            raise ValueError("Missing repository skill: " + name)
        existing = destination / name
        if existing.exists() and tree_hash(existing) != prior.get("skills", {}).get(name):
            raise ValueError("Locally changed skill preserved; merge it before updating: " + name)
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".install-", dir=destination))
    backups = hermes_home / "backups" / "zion-skills" / uuid.uuid4().hex
    changed = []
    try:
        for name in SKILLS:
            shutil.copytree(repo / "skills" / name, staging / name)
            (staging / name / "repository.json").write_text(json.dumps({"repository": str(repo)}, indent=2) + "\n")
        staged_hashes = {name: tree_hash(staging / name) for name in SKILLS}
        for name in SKILLS:
            existing = destination / name
            if existing.exists():
                backups.mkdir(parents=True, exist_ok=True)
                os.replace(existing, backups / name)
            changed.append(name)
            os.replace(staging / name, existing)
        record = {"schema_version": 1, "repository": str(repo), "skills": staged_hashes}
        (staging / "installation.json").write_text(json.dumps(record, indent=2) + "\n")
        os.replace(staging / "installation.json", receipt)
        return {"installed": list(SKILLS), "destination": str(destination), "authority_skill": "preserved"}
    except Exception:
        for name in reversed(changed):
            installed = destination / name
            if installed.exists():
                shutil.rmtree(installed)
            if (backups / name).exists():
                os.replace(backups / name, installed)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-home", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.repo, args.hermes_home), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
