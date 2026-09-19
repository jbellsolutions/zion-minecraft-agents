#!/usr/bin/env python3
"""Advisory evidence review using the owner's approved, budgeted Jev gateway."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

APPROVED_ORIGIN = "https://167.71.241.147.nip.io"
OUTCOMES = {"supported", "contradicted", "insufficient", "unavailable"}


def connection():
    values = {}
    path = Path.home() / ".super-browser.env"
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in ("SUPER_BROWSER_URL", "SUPER_BROWSER_TOKEN"):
                values[key.strip()] = value.strip().strip("\"'")
    for key in ("SUPER_BROWSER_URL", "SUPER_BROWSER_TOKEN"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    if values.get("SUPER_BROWSER_URL", "").rstrip("/") != APPROVED_ORIGIN:
        raise ValueError("Jev connection is not the approved gateway")
    if not values.get("SUPER_BROWSER_TOKEN"):
        raise ValueError("Jev connection is not configured")
    return values["SUPER_BROWSER_TOKEN"]


def call(arguments, status=False, opener=urlopen):
    token = connection()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "advisor_manage" if status else "typesafe_evaluate",
        "arguments": {"operation": "typesafe_status", "arguments": {}} if status else arguments}}
    raw = json.dumps(payload).encode()
    if len(raw) > 32768:
        raise ValueError("Evidence exceeds gateway request limit")
    request = Request(APPROVED_ORIGIN + "/mcp/", data=raw, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"})
    with opener(request, timeout=35) as response:
        response = json.load(response)
    result = response["result"]
    if result.get("isError"):
        raise ValueError("Jev gateway unavailable")
    return json.loads(result["content"][0]["text"])


def evaluate(claim, source, request_id=None, cache=None, caller=call):
    state = {"claim": claim, "source": source}
    digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    request_id = request_id or "zion-evidence-" + digest[:32]
    path = Path(cache) / (digest + ".json") if cache else None
    if path and path.exists():
        previous = json.loads(path.read_text())
        if previous.get("choice") != "unavailable":
            return previous
        request_id = previous["request_id"]
    try:
        result = caller({"purpose": "evidence", "state": state, "request_id": request_id})
        # Preserve the gateway response. Only explicit semantic decisions are accepted.
        decision = result.get("judgment", result.get("result", result))
        choice = decision.get("choice") if isinstance(decision, dict) else None
        if choice == "insufficient_evidence":
            choice = "insufficient"
        if choice not in OUTCOMES:
            choice = "unavailable"
        report = {"choice": choice, "advisory": True, "request_id": request_id,
                  "evidence_sha256": digest, "gateway": result}
    except Exception:
        report = {"choice": "unavailable", "advisory": True, "request_id": request_id,
                  "evidence_sha256": digest, "reason": "gateway_or_budget_unavailable"}
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--status", action="store_true")
    p.add_argument("--evidence-file", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        if args.status:
            result = call({}, status=True)
        else:
            data = json.loads(args.evidence_file.read_text()) if args.evidence_file else json.load(sys.stdin)
            result = evaluate(data["claim"], data["source"], data.get("request_id"),
                              cache=args.output.parent / ".jev-cache" if args.output else None)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return 0 if result.get("choice") != "unavailable" else 1
    except Exception:
        print(json.dumps({"choice": "unavailable", "advisory": True,
                          "reason": "gateway_or_request_unavailable"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
