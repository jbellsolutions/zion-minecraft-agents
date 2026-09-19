#!/usr/bin/env python3
"""Local UI for the same durable jobs used by Hermes and the command line."""
from __future__ import annotations

import http.server
import hashlib
import json
import re
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
UI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
from tools.zion_jobs import JobBusy, JobError, JobRunner, JobStore, TERMINAL
from tools.creation_manifest import confined_path, file_sha256, missing_evidence, read_manifest, validate_manifest
from tools.asset_validation import decode_png

PORT = 8765


class BuilderService:
    def __init__(self, store=None, runner=None, legacy_path=None, installed_path=None):
        self.store = store or JobStore()
        self.runner = runner or JobRunner(self.store)
        self.lock = threading.Lock()
        self.worker = None
        self.legacy_path = Path(legacy_path or PROJECT_DIR / "mods/library.json")
        self.installed_path = Path(installed_path or PROJECT_DIR / ".zion/installed.json")

    def start(self, request=None, job_id=None, action="run"):
        with self.lock:
            if self.worker is not None and self.worker.is_alive():
                raise JobBusy("Still working on your previous creation.")
            if any(job["status"] == "running" for job in self.store.list()):
                raise JobBusy("Another builder is already running. Its status is saved.")
            job = self.store.create(request) if job_id is None else self.store.get(job_id)

            def work():
                try:
                    self.runner.run(job["id"], resume=action == "resume", retry=action == "retry")
                except JobError as exc:
                    if not isinstance(exc, JobBusy):
                        self.store.update(job["id"], status="failed", error=str(exc), text=str(exc))

            self.worker = threading.Thread(target=work, daemon=True)
            self.worker.start()
            return job

    def status(self, job_id=None):
        jobs = self.store.list(1)
        job = self.store.get(job_id) if job_id else (jobs[0] if jobs else None)
        if job is None:
            return {"status": "idle", "text": "Ready to build!", "terminal": True}
        # Exact technical errors remain in the private record and CLI status.
        return {key: job.get(key) for key in ("id", "status", "stage", "text", "attempts", "pending_checks")} | {
            "terminal": job["status"] in TERMINAL,
        }

    def _creation(self, job):
        """Only manifests inside this job, with matching packaged bytes, are public."""
        if not isinstance(job.get("manifest_path"), str):
            raise JobError("This job has no creation manifest yet.")
        manifest = Path(job["manifest_path"]).resolve()
        try:
            manifest.relative_to(self.store.directory(job["id"]).resolve())
        except ValueError as exc:
            raise JobError("Creation manifest leaves its job directory.") from exc
        if validate_manifest(manifest):
            raise JobError("Creation files have not passed validation.")
        data = read_manifest(manifest)
        if data["request"].strip() != job["request"]:
            raise JobError("Creation does not match its saved request.")
        return manifest, data

    def _installed(self, creation_id, manifest_hash, artifact_hashes):
        """An operator receipt and both current installations must match exactly."""
        if not manifest_hash or not artifact_hashes:
            return False
        try:
            data = read_manifest(self.installed_path)
            if data.get("schema_version") != 1 or not isinstance(data.get("installations"), list):
                return False
            for receipt in data["installations"]:
                if not isinstance(receipt, dict) or receipt.get("creation_id") != creation_id or receipt.get("status") != "deployed":
                    continue
                if receipt.get("creation_sha256") != manifest_hash or not isinstance(receipt.get("transaction_id"), str) or not receipt["transaction_id"]:
                    continue
                artifacts = receipt.get("artifacts")
                if not isinstance(artifacts, list) or len(artifacts) != len(artifact_hashes):
                    continue
                if any(not isinstance(entry, dict) or not isinstance(entry.get("sha256"), str) for entry in artifacts):
                    continue
                if {entry["sha256"] for entry in artifacts} != artifact_hashes:
                    continue
                valid = True
                for entry in artifacts:
                    paths = [Path(entry.get(key, "")) for key in ("server_path", "client_path")]
                    if any(not path.is_absolute() or not path.is_file() or path.is_symlink() for path in paths) or paths[0].resolve() == paths[1].resolve():
                        valid = False
                        break
                    if any(file_sha256(path) != entry["sha256"] for path in paths):
                        valid = False
                        break
                if valid:
                    return True
        except (OSError, ValueError, TypeError):
            pass
        return False

    def library(self):
        entries, seen = [], set()
        for job in self.store.list(limit=None):
            try:
                manifest, data = self._creation(job)
            except (JobError, OSError, ValueError):
                continue
            if data["id"] in seen:
                continue
            seen.add(data["id"])
            pending = missing_evidence(data)
            status = "verified" if not pending else "needs_checks"
            if job["status"] in ("running", "queued"):
                status = "building"
            elif job["status"] in ("failed", "cancelled", "interrupted", "awaiting_review"):
                status = job["status"]
            if self._installed(data["id"], file_sha256(manifest), {entry["sha256"] for entry in data["artifacts"]}):
                status = "installed"
            entries.append({"id": data["id"], "job_id": job["id"], "name": data["name"],
                            "description": " ".join(entry["description"] for entry in data["capabilities"])[:500],
                            "type": data["capabilities"][0]["kind"] if len(data["capabilities"]) == 1 else "creation",
                            "icon": f"/jobs/{job['id']}/icon", "built": job["updated_at"], "status": status,
                            "pending_checks": pending, "commands": [entry["literal"] for entry in data["commands"]]})
        try:
            legacy = read_manifest(self.legacy_path).get("mods", []) if self.legacy_path.is_file() else []
        except (OSError, ValueError):
            legacy = []
        for entry in legacy if isinstance(legacy, list) else []:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or entry["id"] in seen:
                continue
            seen.add(entry["id"])
            # Historical 'active' flags are not installation proof.
            status = "verified" if entry.get("status") == "verified" else "legacy"
            hashes = entry.get("artifact_sha256s", [])
            if isinstance(hashes, list) and all(isinstance(digest, str) for digest in hashes):
                if self._installed(entry["id"], entry.get("creation_sha256"), set(hashes)):
                    status = "installed"
            public = {key: entry.get(key) for key in ("id", "name", "description", "type", "icon", "built", "commands")}
            entries.append(public | {"status": status})
        return {"mods": entries}

    def icon(self, job_id):
        manifest, data = self._creation(self.store.get(job_id))
        candidates = sorted((entry for entry in data["assets"] if entry["kind"] in ("thumbnail", "inventory_icon")),
                            key=lambda entry: entry["kind"] != "thumbnail")
        if not candidates:
            raise JobError("This creation has no validated preview.")
        asset = candidates[0]
        body = confined_path(manifest.parent, asset["path"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != asset["sha256"]:
            raise JobError("The preview changed since validation.")
        decode_png(body)
        return body


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    @property
    def builder(self):
        return self.server.builder

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/status":
            try:
                job_id = urllib.parse.parse_qs(url.query).get("id", [None])[0]
                self._json(200, self.builder.status(job_id))
            except JobError as exc:
                self._json(404, {"error": str(exc)})
        elif url.path == "/library":
            self._json(200, self.builder.library())
        elif url.path.startswith("/jobs/"):
            match = re.fullmatch(r"/jobs/([a-f0-9]{32})/icon", url.path)
            if not match:
                self.send_error(404)
                return
            try:
                self._png(self.builder.icon(match.group(1)))
            except (JobError, OSError, ValueError):
                self.send_error(404)
        elif url.path.startswith("/mods/icons/"):
            root = (PROJECT_DIR / "mods/icons").resolve()
            path = (root / urllib.parse.unquote(url.path[len('/mods/icons/'):])).resolve()
            if path.parent != root or path.suffix.lower() != ".png" or not path.is_file():
                self.send_error(404)
            else:
                body = path.read_bytes()
                try:
                    decode_png(body)
                    self._png(body)
                except ValueError:
                    self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get("Host"):
            self._json(403, {"error": "Open this builder in its local browser tab."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32768:
                raise ValueError("Request is empty or too large.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Send a JSON request.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object.")
            if self.path == "/build":
                job = self.builder.start(request=data.get("request"))
                self._json(202, {"status": "started", "id": job["id"]})
            elif self.path == "/cancel":
                self.builder.store.cancel(data.get("id"))
                self._json(200, self.builder.status(data.get("id")))
            elif self.path in ("/resume", "/retry"):
                job = self.builder.start(job_id=data.get("id"), action=self.path[1:])
                self._json(202, {"status": "started", "id": job["id"]})
            else:
                self._json(404, {"error": "Not found"})
        except JobBusy as exc:
            self._json(409, {"error": str(exc)})
        except (JobError, ValueError, UnicodeError) as exc:
            self._json(400, {"error": str(exc)})

    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _png(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.builder = BuilderService()
    print(f"Zion's builder is ready at http://localhost:{PORT}")
    if sys.platform == "darwin":
        subprocess.Popen(["open", f"http://localhost:{PORT}/index.html"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
