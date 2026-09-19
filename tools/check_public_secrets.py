#!/usr/bin/env python3
"""Fail closed on credential-shaped values in files being prepared for publication."""
from pathlib import Path
import re
import subprocess

PATTERNS = [
    re.compile(r"sk-or-v1-[a-fA-F0-9]{64}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


def main():
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], check=True, capture_output=True)
    failures = []
    for name in set(result.stdout.decode().split("\0")) - {""}:
        path = Path(name)
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        if any(pattern.search(text) for pattern in PATTERNS):
            failures.append(name)
    if failures:
        raise SystemExit("Credential-shaped content detected in: " + ", ".join(sorted(failures)))
    print("No credential-shaped values found in publishable files.")


if __name__ == "__main__":
    main()
