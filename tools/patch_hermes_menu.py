#!/usr/bin/env python3
"""Persist /zion in Hermes's capped Telegram menu without replacing core commands.

Preview by default. --apply backs up and narrowly patches the installed menu
collector. This does not call Telegram, read credentials, or change model settings.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

MARKER = "# Zion integration: prioritize its enabled Telegram skill before the menu cap."
ANCHOR = "    # Clamp names; _clamp_command_names works on (name, desc) pairs so we\n"
INSERT = """    # Zion integration: prioritize its enabled Telegram skill before the menu cap.
    # Existing filtering, core/plugin precedence, and other platforms stay intact.
    # Stable sorting preserves the order of every other skill.
    if platform == "telegram":
        skill_triples.sort(key=lambda entry: entry[2] != "/zion")

"""


def transform(source):
    if MARKER in source:
        if source.count(MARKER) != 1 or INSERT not in source:
            raise ValueError("Existing Zion menu patch differs; inspect it before updating")
        return source
    if source.count(ANCHOR) != 1:
        raise ValueError("Hermes menu collector changed; review the new implementation before patching")
    updated = source.replace(ANCHOR, INSERT + ANCHOR, 1)
    ast.parse(updated)
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-root", required=True, type=Path)
    parser.add_argument("--hermes-home", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    path = args.hermes_root.expanduser().resolve() / "hermes_cli/commands.py"
    try:
        if path.is_symlink():
            raise ValueError("The command source must be a regular file")
        original = path.read_bytes()
        updated = transform(original.decode()).encode()
        result = {"changed": updated != original, "before_sha256": hashlib.sha256(original).hexdigest(), "after_sha256": hashlib.sha256(updated).hexdigest(), "applied": False}
        if args.apply and updated != original:
            backup = args.hermes_home.expanduser().resolve() / "backups/zion-telegram-menu" / uuid.uuid4().hex / "commands.py"
            backup.parent.mkdir(parents=True, mode=0o700)
            with backup.open("xb") as stream:
                os.chmod(backup, 0o600)
                stream.write(original)
            temporary = path.with_name(".commands." + uuid.uuid4().hex + ".tmp")
            try:
                temporary.write_bytes(updated)
                os.chmod(temporary, path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            result.update(applied=True, backup=str(backup))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, SyntaxError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
