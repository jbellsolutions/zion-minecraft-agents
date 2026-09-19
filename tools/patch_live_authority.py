#!/usr/bin/env python3
"""Narrowly correct legacy operational advice without exporting a private learned skill.

Default is a counts/hash preview. --apply creates a private backup, then patches
only pack format literals and unsafe process/session-lock guidance. Other learned
content stays in place. The public repository never receives the private skill.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

MARKER = "<!-- zion-supercharge-operational-contract-v1 -->"
CONTRACT = """
<!-- zion-supercharge-operational-contract-v1 -->
## Current Zion build and deployment contract

Use the installed `zion` skill for durable jobs and repository tooling. Preserve
the learned Forge patterns below, with these operational corrections taking precedence:

- Target Minecraft 1.21.4, Forge 54.1.0, Java 21, Gradle 8.8. Resource-pack format
  is 46; data-pack format is 61. Inventory item definitions and real artwork are mandatory.
- Route build/room/house/vehicle/icon/repair/library/status/cancel/rollback through
  `/zion`; generated features also require meaningful in-game slash commands.
- Create and check artwork before deployment with the configured `zion_art.py` path.
  Complete the creation manifest, source guards, compiled artifact, and runtime evidence.
- Use `tools/zion_deploy.py` with the private runtime configuration for backup,
  install, stop/start, and rollback. It tracks exact server/client files and process
  ownership. Never use broad process termination, force kills, or delete session.lock.
  Never replace entire mods or world folders. Preserve existing registry IDs on updates.
- Compute structure plans off-thread only when useful; place blocks, spawn entities,
  and access mutable Minecraft world state on the server thread in bounded batches.
- Jev is an optional requirements/evidence reviewer via the configured gateway;
  an outage is unavailable verification, not a passed check or a blocked local build.
- Keep source and job state in persistent workspaces. Server-ready and client-rendered
  are separate checks. Do not promise visual success from a compiler exit code.

"""


def transform(text):
    counts = {"pack_format": 0, "unsafe_shell_blocks": 0, "unsafe_advice_lines": 0}
    text, counts["pack_format"] = re.subn(r'(pack_format[\s`"\':=]+)48\b', r'\g<1>46', text)
    dangerous = re.compile(r"\bpkill\b|\bkillall\b|\bkill\s+-9\b|\brm\b[^\n]*session\.lock|kill\s*\+\s*rm\s+session\.lock")

    def fence(match):
        language, body = match.group(1), match.group(2)
        if language.strip() in {"bash", "sh", "shell", "zsh", ""} and dangerous.search(body):
            counts["unsafe_shell_blocks"] += 1
            return ("Use `tools/zion_deploy.py` from the repository recorded by the installed\n"
                    "`zion` skill, with the private runtime configuration. Check/adopt the exact\n"
                    "server process before a graceful stop; use its transaction rollback on failure.\n")
        return match.group(0)

    text = re.sub(r"^```([^\n]*)\n(.*?)^```[ \t]*$", fence, text, flags=re.M | re.S)
    lines = []
    for line in text.splitlines(keepends=True):
        if dangerous.search(line):
            counts["unsafe_advice_lines"] += 1
            lines.append("Use verified graceful server control through `tools/zion_deploy.py`; preserve session.lock.\n")
        else:
            lines.append(line)
    text = "".join(lines)
    if MARKER not in text:
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end == -1:
                raise ValueError("Unclosed skill frontmatter")
            end = text.find("\n", end + 1)
            text = text[:end + 1] + CONTRACT + text[end + 1:]
        else:
            text = CONTRACT + text
    return text, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-home", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    home = args.hermes_home.expanduser().resolve()
    path = home / "skills/gaming/minecraft-forge-authority/SKILL.md"
    try:
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("Authority path must not traverse symlinks")
        original = path.read_bytes()
        updated, counts = transform(original.decode())
        encoded = updated.encode()
        result = {"changes": counts, "changed": encoded != original, "before_sha256": hashlib.sha256(original).hexdigest(), "after_sha256": hashlib.sha256(encoded).hexdigest(), "applied": False}
        if args.apply and original != encoded:
            backup = home / "backups/zion-authority" / uuid.uuid4().hex / "SKILL.md"
            backup.parent.mkdir(parents=True, mode=0o700)
            with backup.open("xb") as stream:
                os.chmod(backup, 0o600)
                stream.write(original)
            temporary = path.with_name(".SKILL." + uuid.uuid4().hex + ".tmp")
            temporary.write_bytes(encoded)
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
            result.update(applied=True, backup=str(backup))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
