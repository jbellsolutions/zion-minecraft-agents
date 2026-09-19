#!/usr/bin/env python3
"""Build-only Hermes adapter for the shared durable job runner."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = "z-ai/glm-5.3-flash"


def executable():
    candidates = [os.environ.get("HERMES_EXECUTABLE"), shutil.which("hermes"),
                  str(Path.home() / ".hermes/hermes-agent/venv/bin/hermes")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("Hermes is not installed on this builder host")


def redact(text):
    text = re.sub(r"sk-[A-Za-z0-9_-]{16,}", "[redacted]", text)
    text = re.sub(r"\b\d{8,12}:[A-Za-z0-9_-]{25,}\b", "[redacted]", text)
    for name, value in os.environ.items():
        if any(word in name.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY")) and len(value) > 7:
            text = text.replace(value, "[redacted]")
    return text


def build_prompt(request, output):
    return f"""Build Zion's Minecraft creation using real coding tools.
Request: {request['request']}
Preserve this request verbatim in creation.json's request field.
Attempt: {request.get('attempt', 1)}. Previous failure: {request.get('previous_error') or 'none'}.
All creation files MUST be written inside this job directory: {output}
Repository with reusable tools/templates: {ROOT}
Read {ROOT}/docs/supercharge-plan.md and {ROOT}/skills/hermes-minecraft-superbuilder/SKILL.md.
Read {ROOT}/schemas/creation-v1.schema.json and {ROOT}/tools/creation_manifest.py.
Create output/creation.json at {output}/creation.json, schema_version 1, with target
Minecraft 1.21.4 Forge54.1.0 Java21, capabilities, hashed assets, per-capability /zion
commands, hashed artifacts and evidence. Preserve existing IDs when repairing.
Use a dedicated image tool: {sys.executable} {ROOT}/tools/zion_art.py --help.
Inventory icons need transparent 64x64 RGBA art and recognisable silhouettes.
Furniture requires geometry and working interactions, vehicles require visible models.
Use the Gradle wrapper, asset guards, and real compiler. Repair failed stages at most
three times, retaining diagnostics. A missing API key or failed generator is a failure,
never permission to insert a colored square. Broader requests may need multiple assets.
Do NOT install into a live client/server, restart services, change bot settings, modify
worlds, delete other jobs, or send Telegram messages. This invocation only builds.
Do NOT invoke zion_jobs recursively. The outer runner owns this job.
Record only tests actually run. Missing client/gameplay checks stay pending. Evidence
must name the exact artifact SHA256. An HTTP success or your judgment is not game proof.
When files are built, finish with a concise summary. The outer runner validates them.
"""


def run(request_file, output):
    request = json.loads(Path(request_file).read_text())
    if request.get("schema_version") != 1 or not isinstance(request.get("request"), str) or not request["request"].strip():
        raise ValueError("Invalid job request")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    argv = [executable(), "chat", "--query", build_prompt(request, output),
            "--model", MODEL, "--provider", "openrouter", "--quiet", "--max-turns", "90"]
    # The outer runner starts this process in a process group and owns cancellation.
    result = subprocess.run(argv, cwd=output, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    (output / "provider.log").write_text(redact(result.stdout or ""))
    if result.returncode:
        raise RuntimeError(f"Coding provider failed (exit {result.returncode}); see provider.log")
    if not (output / "creation.json").is_file():
        raise RuntimeError("Coding provider did not produce a creation manifest")
    print(json.dumps({"status": "generated", "manifest": "creation.json", "model": MODEL}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request-file", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    try:
        run(args.request_file, args.output_dir)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "failed", "error": redact(str(error))}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
