#!/usr/bin/env python3
"""Durable build jobs shared by the CLI and web UI. No deployment is inferred."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

try:
    from .creation_manifest import missing_evidence, read_manifest, validate_manifest
    from .zion_jev import evaluate as review_evidence
except ImportError:
    from creation_manifest import missing_evidence, read_manifest, validate_manifest
    from zion_jev import evaluate as review_evidence

PROJECT_DIR = Path(__file__).resolve().parent.parent
MAX_ATTEMPTS = 3
TERMINAL = {"succeeded", "failed", "cancelled", "interrupted", "awaiting_verification", "awaiting_review"}
IDENTIFIER = re.compile(r"^[a-f0-9]{32}$")


class JobError(RuntimeError):
    pass


class JobBusy(JobError):
    pass


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def redact(text):
    text = str(text)
    for key, value in os.environ.items():
        if re.search(r"TOKEN|PASSWORD|SECRET|API_KEY", key) and len(value) >= 8:
            text = text.replace(value, "[redacted]")
    text = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{12,}|[0-9]{7,}:[A-Za-z0-9_-]{20,})\b", "[redacted]", text)
    return text


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def file_lock(path, blocking=True):
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as exc:
            raise JobBusy("A worker is already running this job.") from exc
        try:
            yield stream
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class JobStore:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("ZION_JOBS_DIR", PROJECT_DIR / ".zion/jobs")).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def directory(self, job_id):
        if not isinstance(job_id, str) or not IDENTIFIER.fullmatch(job_id):
            raise JobError("Invalid job ID.")
        path = self.root / job_id
        if not path.is_dir():
            raise JobError("Job not found.")
        return path

    def create(self, request, options=None):
        if not isinstance(request, str) or not request.strip() or len(request) > 8000:
            raise JobError("Describe a creation in 1–8000 characters.")
        if options is not None and not isinstance(options, dict):
            raise JobError("Job options must be an object.")
        ident = uuid.uuid4().hex
        directory = self.root / ident
        directory.mkdir(mode=0o700)
        now = timestamp()
        job = {"schema_version": 1, "id": ident, "request": request.strip(), "options": options or {},
               "status": "queued", "stage": "generate", "attempts": 0, "max_attempts": MAX_ATTEMPTS,
               "created_at": now, "updated_at": now, "cancel_requested": False,
               "text": "Your creation is queued.", "error": None, "manifest_path": None,
               "events": [{"at": now, "status": "queued"}]}
        atomic_json(directory / "job.json", job)
        return job

    def _read(self, directory):
        try:
            return json.loads((directory / "job.json").read_text())
        except (OSError, ValueError) as exc:
            raise JobError("The saved job record is unreadable; its files have been preserved.") from exc

    def update(self, job_id, **changes):
        directory = self.directory(job_id)
        with file_lock(directory / "record.lock"):
            job = self._read(directory)
            previous = job["status"]
            job.update(changes)
            job["updated_at"] = timestamp()
            if job["status"] != previous:
                job["events"].append({"at": job["updated_at"], "status": job["status"]})
            atomic_json(directory / "job.json", job)
            return job

    def get(self, job_id, recover=True):
        directory = self.directory(job_id)
        job = self._read(directory)
        if recover and job["status"] == "running":
            try:
                with file_lock(directory / "run.lock", blocking=False):
                    job = self._read(directory)
                    if job["status"] == "running":
                        job = self.update(job_id, status="interrupted", text="The previous worker stopped. This job can be resumed.")
            except JobBusy:
                pass
        return job

    def list(self, limit=30):
        jobs = []
        for directory in self.root.iterdir():
            if directory.is_dir() and IDENTIFIER.fullmatch(directory.name):
                try:
                    jobs.append(self.get(directory.name))
                except JobError:
                    continue
        return sorted(jobs, key=lambda job: job["created_at"], reverse=True)[:limit]

    def cancel(self, job_id):
        job = self.get(job_id)
        if job["status"] in ("succeeded", "cancelled"):
            return job
        if job["status"] == "running":
            return self.update(job_id, cancel_requested=True, text="Stopping this build safely…")
        return self.update(job_id, status="cancelled", cancel_requested=True, text="Build cancelled. Existing game files were not changed.")


class JobRunner:
    def __init__(self, store=None, provider_command=None, timeout=3600, poll_interval=0.2, reviewer=review_evidence):
        self.store = store or JobStore()
        if provider_command is None:
            configured = os.environ.get("ZION_PROVIDER_COMMAND")
            provider_command = json.loads(configured) if configured else [sys.executable, str(PROJECT_DIR / "tools/zion_provider.py")]
        if not isinstance(provider_command, list) or not provider_command or not all(isinstance(x, str) and x for x in provider_command):
            raise JobError("Provider command must be a nonempty JSON array of arguments.")
        self.provider_command = provider_command
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.reviewer = reviewer

    def _verify(self, job_id, manifest):
        job = self.store.get(job_id, recover=False)
        if job["cancel_requested"]:
            return self.store.update(job_id, status="cancelled", text="Build cancelled. No deployment was performed.")
        issues = validate_manifest(manifest)
        if issues:
            return self.store.update(job_id, status="failed", stage="validate", error="\n".join(issues),
                                     text="The creation did not pass validation. Its files and exact errors are saved.")
        data = read_manifest(manifest)
        if data["request"].strip() != job["request"]:
            return self.store.update(job_id, status="failed", stage="validate", error="Manifest request differs from the original job request.",
                                     text="The creation does not match the saved request. Its files were preserved for repair.")
        self.store.update(job_id, stage="review", text="Checking the requested features against the saved evidence…")
        summary = {"capabilities": data["capabilities"], "commands": data["commands"],
                   "evidence": [{key: entry.get(key) for key in ("check", "status", "artifact_sha256")} for entry in data["evidence"]],
                   "artifact_sha256": [entry["sha256"] for entry in data["artifacts"]]}
        try:
            report = self.reviewer(claim=redact("The completed creation satisfies this request: " + job["request"]),
                                   source=redact(json.dumps(summary, ensure_ascii=True))[:16000],
                                   cache=self.store.directory(job_id) / ".jev-cache")
        except Exception:
            report = {"choice": "unavailable", "advisory": True, "reason": "review_unavailable"}
        if not isinstance(report, dict) or report.get("choice") not in ("supported", "contradicted", "insufficient", "unavailable"):
            report = {"choice": "unavailable", "advisory": True, "reason": "invalid_review_response"}
        report = json.loads(redact(json.dumps(report)))
        report_path = self.store.directory(job_id) / "jev-review.json"
        atomic_json(report_path, report)
        self.store.update(job_id, semantic_review={"choice": report["choice"], "advisory": True, "path": str(report_path)})
        if self.store.get(job_id, recover=False)["cancel_requested"]:
            return self.store.update(job_id, status="cancelled", text="Build cancelled. No deployment was performed.")
        pending = missing_evidence(data)
        if report["choice"] == "contradicted":
            return self.store.update(job_id, status="failed", stage="review", error="Jev found a mismatch between the request and evidence.",
                                     pending_checks=pending, text="The requirement review found a mismatch. The creation needs repair before installation.")
        if report["choice"] == "insufficient":
            return self.store.update(job_id, status="awaiting_review", stage="review", error=None,
                                     pending_checks=pending, text="Built, but the requirement review needs more evidence. It has not been installed.")
        note = " Jev review is unavailable; deterministic checks remain authoritative." if report["choice"] == "unavailable" else ""
        if pending:
            return self.store.update(job_id, status="awaiting_verification", stage="verify", error=None,
                                     pending_checks=pending, text="Built, but not installed. Still needs: " + ", ".join(pending) + "." + note)
        return self.store.update(job_id, status="succeeded", stage="verified", error=None, pending_checks=[],
                                 text="Build verified and ready for installation. No deployment has been performed by this job." + note)

    @staticmethod
    def _stop(process):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        except ProcessLookupError:
            pass

    def run(self, job_id, *, resume=False, retry=False):
        directory = self.store.directory(job_id)
        with file_lock(directory / "run.lock", blocking=False) as lock:
            job = self.store.get(job_id, recover=False)
            if job["status"] == "succeeded":
                return job
            if job["status"] == "cancelled" and not resume:
                raise JobError("This job was cancelled; resume it explicitly to continue.")
            if job["status"] in ("failed", "interrupted", "running") and not (retry or resume):
                raise JobError("Use retry or resume to continue this saved job.")
            if resume and job.get("manifest_path") and Path(job["manifest_path"]).is_file():
                self.store.update(job_id, status="running", cancel_requested=False, stage="validate")
                return self._verify(job_id, Path(job["manifest_path"]))
            if job["status"] in ("awaiting_verification", "awaiting_review") and not retry:
                self.store.update(job_id, status="running", cancel_requested=False, stage="validate")
                return self._verify(job_id, Path(job["manifest_path"]))
            if job["attempts"] >= MAX_ATTEMPTS:
                raise JobError("This job has reached its three-attempt repair limit. Review the saved errors before creating a new job.")
            attempt = job["attempts"] + 1
            output = directory / f"attempt-{attempt}" / "output"
            output.mkdir(parents=True, mode=0o700)
            request_file = output.parent / "request.json"
            atomic_json(request_file, {"schema_version": 1, "job_id": job_id, "request": job["request"],
                                       "attempt": attempt, "previous_error": job.get("error"), "options": job.get("options", {})})
            manifest = output / "creation.json"
            self.store.update(job_id, status="running", stage="generate", attempts=attempt,
                              cancel_requested=False, error=None, manifest_path=str(manifest),
                              semantic_review=None, pending_checks=[],
                              text=f"Building your creation (attempt {attempt} of {MAX_ATTEMPTS})…")
            command = self.provider_command + ["--request-file", str(request_file), "--output-dir", str(output)]
            process, reader = None, None
            captured = bytearray()
            try:
                process = subprocess.Popen(command, cwd=PROJECT_DIR, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           start_new_session=True, pass_fds=(lock.fileno(),))
                self.store.update(job_id, provider_pid=process.pid)

                def consume():
                    while True:
                        chunk = process.stdout.read(4096)
                        if not chunk:
                            break
                        captured.extend(chunk)
                        if len(captured) > 1024 * 1024:
                            del captured[:-1024 * 1024]

                reader = threading.Thread(target=consume, daemon=True)
                reader.start()
                deadline = time.monotonic() + self.timeout
                stopped = None
                while process.poll() is None:
                    if self.store.get(job_id, recover=False)["cancel_requested"]:
                        stopped = "cancelled"
                        break
                    if time.monotonic() >= deadline:
                        stopped = "timeout"
                        break
                    time.sleep(self.poll_interval)
                if stopped:
                    self._stop(process)
                reader.join(timeout=5)
                self.store.update(job_id, provider_pid=None)
                output_text = redact(captured.decode("utf-8", "replace"))
                log = output.parent / "provider.log"
                log.write_text(output_text, encoding="utf-8")
                log.chmod(0o600)
                if stopped == "cancelled" or self.store.get(job_id, recover=False)["cancel_requested"]:
                    return self.store.update(job_id, status="cancelled", text="Build cancelled. No deployment was performed.")
                if stopped == "timeout":
                    return self.store.update(job_id, status="failed", error=f"Provider timed out after {self.timeout} seconds.",
                                             text="The build timed out and was stopped. It has not been installed.")
                if process.returncode:
                    return self.store.update(job_id, status="failed", error=f"Provider exited with status {process.returncode}.\n{output_text[-6000:]}",
                                             text="The builder reported an error. Nothing has been marked complete.")
                if not manifest.is_file():
                    return self.store.update(job_id, status="failed", error="Provider exited successfully but did not produce creation.json.",
                                             text="The builder did not produce a verifiable creation. It has not been installed.")
                self.store.update(job_id, stage="validate", text="Checking files, artwork and verification evidence…")
                return self._verify(job_id, manifest)
            except (KeyboardInterrupt, SystemExit):
                if process:
                    self._stop(process)
                self.store.update(job_id, status="interrupted", provider_pid=None, text="Build interrupted. Its progress is saved for resume.")
                raise
            except Exception as exc:
                if process:
                    self._stop(process)
                return self.store.update(job_id, status="failed", provider_pid=None, error=redact(str(exc)),
                                         text="The build stopped with an error. Its progress and error are saved.")
            finally:
                if reader:
                    reader.join(timeout=1)
                if process and process.stdout:
                    process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-dir", type=Path)
    parser.add_argument("--provider-command", help="JSON argv array; no shell interpolation")
    parser.add_argument("--timeout", type=float, default=3600)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "build"):
        command = commands.add_parser(name)
        command.add_argument("request")
    commands.add_parser("list")
    for name in ("status", "run", "cancel", "resume", "retry"):
        command = commands.add_parser(name)
        command.add_argument("job_id")
    args = parser.parse_args()
    try:
        store = JobStore(args.jobs_dir)
        if args.command == "list":
            result = store.list()
        elif args.command in ("create", "build"):
            result = store.create(args.request)
        else:
            result = store.get(args.job_id)
        if args.command == "cancel":
            result = store.cancel(args.job_id)
        if args.command in ("build", "run", "resume", "retry"):
            provider = json.loads(args.provider_command) if args.provider_command else None
            runner = JobRunner(store, provider, timeout=args.timeout)
            result = runner.run(result["id"], resume=args.command == "resume", retry=args.command == "retry")
        print(json.dumps(result, indent=2))
        return 1 if isinstance(result, dict) and result.get("status") in ("failed", "interrupted") else 0
    except (JobError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
