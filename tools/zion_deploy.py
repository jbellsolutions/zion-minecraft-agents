#!/usr/bin/env python3
"""Exact-file Minecraft deployments with persistent backups and verified process ownership.

Private runtime configuration and transaction journals never belong in Git. No shell
commands, directory replacement, force kills, or world/session.lock deletion are used.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import zipfile

try:
    from .creation_manifest import validate_manifest
except ImportError:
    try:
        from tools.creation_manifest import validate_manifest
    except ImportError:
        from creation_manifest import validate_manifest


class DeployError(RuntimeError):
    pass


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def copy_atomic(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name("." + target.name + "." + uuid.uuid4().hex)
    try:
        with open(source, "rb") as src, temporary.open("xb") as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def regular_path(path):
    """Reject symlink traversal even when a link currently points inside the root."""
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise DeployError("Symlink paths are not supported: " + str(path))
    if path.exists() and not path.is_file():
        raise DeployError("Expected a regular file: " + str(path))
    return path


def basename(value, extension):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*" + re.escape(extension), value):
        raise DeployError("Invalid artifact filename")
    return value


def check_archive(path, kind):
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len({i.filename for i in infos}) != len(infos):
                raise DeployError("Duplicate archive entries")
            if sum(i.file_size for i in infos) > 512 * 1024 * 1024:
                raise DeployError("Artifact exceeds the 512 MiB unpacked limit")
            if any(i.filename.startswith("/") or ".." in Path(i.filename).parts for i in infos):
                raise DeployError("Unsafe archive path")
            if archive.testzip():
                raise DeployError("Corrupt artifact")
            names = {i.filename for i in infos}
            if kind == "mod":
                if "META-INF/mods.toml" not in names or not any(n.endswith(".class") for n in names):
                    raise DeployError("Mod must contain Forge metadata and compiled classes")
            else:
                meta = json.loads(archive.read("pack.mcmeta"))
                if meta.get("pack", {}).get("pack_format") != 61:
                    raise DeployError("Datapack must have pack_format 61 at its archive root")
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise DeployError("Invalid " + kind + " artifact") from exc


class Runtime:
    def __init__(self, config):
        self.config = config
        self.server = Path(config["server_root"]).expanduser().absolute()
        self.client = Path(config["client_mods"]).expanduser().absolute()
        if not self.server.is_dir() or not self.client.is_dir():
            raise DeployError("Existing server_root and client_mods directories are required")
        self.state = self.server / ".zion-deploy"
        regular_path(self.state / "ownership.json")
        regular_path(self.client / ".check")
        self.timeout = float(config.get("startup_timeout_seconds", 180))
        self.stop_timeout = float(config.get("stop_timeout_seconds", 90))

    @contextlib.contextmanager
    def lock(self):
        self.state.mkdir(mode=0o700, exist_ok=True)
        lock_path = regular_path(self.state / "deployment.lock")
        with lock_path.open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise DeployError("Another deployment owns the server lock") from exc
            yield

    def process(self, pid):
        if not isinstance(pid, int) or pid < 2:
            return None
        result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart=", "-o", "comm="], capture_output=True, text=True)
        line = result.stdout.strip()
        parts = line.split(None, 5)
        if result.returncode or len(parts) != 6:
            return None
        if Path(parts[5]).name.lower() != "java":
            return None
        if self.process_cwd(pid) != self.server.resolve():
            return None
        return {"pid": pid, "started": " ".join(parts[:5]), "server_root": str(self.server.resolve())}

    def process_cwd(self, pid):
        cwd = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True)
        dirs = [p[1:] for p in cwd.stdout.splitlines() if p.startswith("n")]
        return Path(dirs[0]).resolve() if len(dirs) == 1 else None

    def running(self):
        ps = subprocess.run(["ps", "-axo", "pid=,comm="], capture_output=True, text=True, check=True)
        found = []
        for line in ps.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and Path(parts[1]).name.lower() == "java":
                process = self.process(int(parts[0]))
                if process:
                    found.append(process)
        return found

    def owned(self):
        running = self.running()
        if not running:
            return None
        record = self.state / "ownership.json"
        owner = read_json(record) if record.exists() else None
        if len(running) != 1 or running[0] != owner:
            raise DeployError("A server process is running without verified ownership; adopt its exact PID first")
        return owner

    def client_processes(self):
        """Inspect arguments privately; never return access tokens or launch argv."""
        ps = subprocess.run(["ps", "-axo", "pid=,comm="], capture_output=True, text=True, check=True)
        found = []
        for line in ps.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) != 2 or Path(parts[1]).name.lower() != "java":
                continue
            pid = int(parts[0])
            args = subprocess.run(["ps", "-p", str(pid), "-o", "args="], capture_output=True, text=True).stdout
            game = re.search(r"--gameDir(?:=|\s+)(.+?)(?=\s+--|$)", args)
            if game:
                game_path = Path(game.group(1).strip().strip('\"')).expanduser()
                if not game_path.is_absolute():
                    cwd = self.process_cwd(pid)
                    if cwd is None:
                        raise DeployError("Cannot identify a Minecraft client's relative game directory")
                    game_path = cwd / game_path
            elif "net.minecraft.client.main.Main" in args or re.search(r"--launchTarget\s+forgeclient\b", args):
                game_path = self.process_cwd(pid)
                if game_path is None:
                    raise DeployError("Cannot identify a Minecraft client's default game directory")
            else:
                continue
            if game_path.resolve() != self.client.parent.resolve():
                continue
            started = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True).stdout.strip()
            if started:
                found.append({"pid": pid, "started": started})
        return found

    def stop_client(self, allowed=False):
        clients = self.client_processes()
        if clients and not allowed:
            raise DeployError("The affected Minecraft client is open; use --stop-client for a graceful close before installing")
        for client in clients:
            if client not in self.client_processes():
                raise DeployError("Client process identity changed before shutdown")
            os.kill(client["pid"], signal.SIGTERM)
        deadline = time.monotonic() + self.stop_timeout
        while self.client_processes():
            if time.monotonic() >= deadline:
                raise DeployError("Client did not close gracefully; files remain unchanged")
            time.sleep(0.25)
        return bool(clients)

    def adopt(self, pid):
        found = self.running()
        if len(found) != 1 or found[0]["pid"] != pid:
            raise DeployError("PID must be the sole Java process whose working directory is this server")
        atomic_json(self.state / "ownership.json", found[0])
        return found[0]

    def stop(self):
        owner = self.owned()
        if not owner:
            return
        # Recheck identity immediately before signaling. SIGTERM runs Minecraft's
        # shutdown hook; a timeout leaves files untouched and requires investigation.
        if self.process(owner["pid"]) != owner:
            raise DeployError("Server ownership changed before shutdown")
        os.kill(owner["pid"], signal.SIGTERM)
        deadline = time.monotonic() + self.stop_timeout
        while time.monotonic() < deadline:
            if self.process(owner["pid"]) != owner:
                if self.running():
                    raise DeployError("Another server appeared during shutdown")
                return
            time.sleep(0.25)
        raise DeployError("Graceful shutdown timed out; no force kill or lock deletion attempted")

    def start(self):
        if self.owned():
            raise DeployError("Server is already running")
        argv = self.config.get("start_argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) for x in argv):
            raise DeployError("start_argv must be the exact Java argument array")
        if Path(argv[0]).name.lower() != "java":
            raise DeployError("start_argv must launch Java directly, without a shell wrapper")
        log = self.state / "starts" / (uuid.uuid4().hex + ".log")
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("xb") as stream:
            child = subprocess.Popen(argv, cwd=self.server, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        # Each launch has a new log; an old 'Done' cannot satisfy readiness.
        deadline = time.monotonic() + self.timeout
        ownership = None
        offset = 0
        tail = ""
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise DeployError("Server exited before readiness; see its private launch log")
            if ownership is None:
                ownership = self.process(child.pid)
                if ownership:
                    atomic_json(self.state / "ownership.json", ownership)
            with log.open() as stream:
                stream.seek(offset)
                tail = (tail + stream.read())[-8192:]
                offset = stream.tell()
            if ownership and re.search(r'Done \([^)]+\)! For help, type "help"', tail):
                return {"pid": child.pid, "log": str(log), "ready": True}
            time.sleep(0.25)
        raise DeployError("Server readiness timed out; see its private launch log")


def build_plan(runtime, manifest, base):
    if manifest.get("schema_version") != 1 or manifest.get("minecraft") != "1.21.4" or manifest.get("forge") != "54.1.0":
        raise DeployError("Deployment manifest must target Minecraft 1.21.4 / Forge 54.1.0")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", manifest.get("job_id", "")):
        raise DeployError("A safe job_id is required")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise DeployError("No artifacts to deploy")
    creation_path = regular_path(Path(base) / manifest.get("creation_manifest", ""))
    if not creation_path.is_file() or digest(creation_path) != manifest.get("creation_sha256"):
        raise DeployError("Deployment requires an exact hashed creation manifest")
    issues = validate_manifest(creation_path, require_evidence=False)
    if issues:
        raise DeployError("Creation validation failed: " + "; ".join(issues[:8]))
    creation = read_json(creation_path)
    available = {(str((creation_path.parent / a["path"]).resolve()), a["sha256"], "mod" if a["kind"] == "jar" else "datapack") for a in creation["artifacts"]}
    compile_hashes = {e.get("artifact_sha256") for e in creation.get("evidence", []) if e.get("check") == "compile" and e.get("status") == "passed"}
    changes = {}
    for artifact in artifacts:
        kind = artifact.get("kind")
        if kind not in {"mod", "datapack"}:
            raise DeployError("Artifact kind must be mod or datapack")
        extension = ".jar" if kind == "mod" else ".zip"
        name = basename(artifact.get("filename"), extension)
        source = regular_path(Path(base) / artifact["source"])
        if not source.is_file() or digest(source) != artifact.get("sha256"):
            raise DeployError("Artifact hash mismatch")
        if (str(source.resolve()), artifact["sha256"], kind) not in available:
            raise DeployError("Artifact is not in the validated creation manifest")
        if kind == "mod" and artifact["sha256"] not in compile_hashes:
            raise DeployError("Mod requires passed hash-linked compile evidence")
        check_archive(source, kind)
        if kind == "mod":
            destinations = [runtime.server / "mods", runtime.client]
        else:
            level = runtime.config.get("level_name", "world")
            if not isinstance(level, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", level):
                raise DeployError("Configure a safe level_name for datapacks")
            destinations = [runtime.server / level / "datapacks"]
        replacements = {}
        for replacement in artifact.get("replaces", []):
            oldname = basename(replacement.get("filename"), extension)
            oldhash = replacement.get("sha256", "")
            if not re.fullmatch(r"[0-9a-f]{64}", oldhash) or oldname in replacements:
                raise DeployError("Invalid or duplicate replacement hash")
            replacements[oldname] = oldhash
        for directory in destinations:
            target = regular_path(directory / name)
            for oldname, expected in replacements.items():
                old = regular_path(directory / oldname)
                if old.exists() and digest(old) != expected:
                    raise DeployError("Replacement hash mismatch: " + str(old))
                if old != target and old.exists():
                    if str(old) in changes:
                        raise DeployError("Overlapping artifact targets")
                    changes[str(old)] = {"target": str(old), "source": None, "after": None}
            if target.exists() and digest(target) != artifact["sha256"] and replacements.get(name) != digest(target):
                raise DeployError("Existing artifact needs an explicit replacement hash: " + str(target))
            if str(target) in changes:
                raise DeployError("Overlapping artifact targets")
            changes[str(target)] = {"target": str(target), "source": str(source), "after": artifact["sha256"]}
    return list(changes.values())


def save_journal(directory, journal):
    atomic_json(directory / "journal.json", journal)


def world_inventory(runtime):
    level = runtime.config.get("level_name", "world")
    if not isinstance(level, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", level):
        raise DeployError("Configure a safe level_name")
    root = runtime.server / level
    regular_path(root / ".path-check")
    files = {}
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise DeployError("World snapshot refuses symlinks")
            if path.is_file() and path.name != "session.lock":
                regular_path(path)
                files[str(path.relative_to(root))] = digest(path)
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return root, files, fingerprint


def snapshot_world(runtime, directory, journal):
    root, files, fingerprint = world_inventory(runtime)
    for relative in files:
        copy_atomic(root / relative, directory / "world" / relative)
        if digest(directory / "world" / relative) != files[relative]:
            raise DeployError("World changed during its stopped snapshot")
    # Include gameplay/server configuration, while excluding credentials unrelated
    # to Minecraft and all logs. Backups stay private on this server.
    configs = []
    for name in ("server.properties", "ops.json", "whitelist.json", "banned-ips.json", "banned-players.json"):
        path = runtime.server / name
        if path.is_file():
            configs.append(path)
    for name in ("config", "defaultconfigs"):
        folder = runtime.server / name
        if folder.exists():
            regular_path(folder / ".path-check")
            configs.extend(p for p in folder.rglob("*") if p.is_file())
    config_files = {}
    for path in configs:
        regular_path(path)
        relative = str(path.relative_to(runtime.server))
        config_files[relative] = digest(path)
        copy_atomic(path, directory / "server-config" / relative)
        if digest(directory / "server-config" / relative) != config_files[relative]:
            raise DeployError("Configuration changed during its stopped snapshot")
    journal["world_snapshot"] = {"root": str(root), "files": files, "fingerprint": fingerprint, "config_files": config_files}
    save_journal(directory, journal)


def restore_world(runtime, directory, journal, expected_fingerprint):
    if runtime.running():
        raise DeployError("World restoration requires the server to be stopped")
    root, current, fingerprint = world_inventory(runtime)
    saved = journal.get("world_snapshot")
    if not saved or str(root) != saved["root"] or fingerprint != expected_fingerprint:
        raise DeployError("World restore requires the exact current stopped-world fingerprint")
    for relative, expected in saved["files"].items():
        backup = regular_path(directory / "world" / relative)
        if not backup.is_file() or digest(backup) != expected:
            raise DeployError("World backup verification failed")
    for relative, expected in saved["config_files"].items():
        backup = regular_path(directory / "server-config" / relative)
        if not backup.is_file() or digest(backup) != expected:
            raise DeployError("Server configuration backup verification failed")
    for relative in current.keys() - saved["files"].keys():
        regular_path(root / relative).unlink()
    for relative in saved["files"]:
        copy_atomic(directory / "world" / relative, regular_path(root / relative))
    for relative in saved["config_files"]:
        copy_atomic(directory / "server-config" / relative, regular_path(runtime.server / relative))


def restore_files(directory, journal, runtime):
    # Validate every current file and backup before touching any file. Refuse to
    # undo another later deployment or a player's manual change.
    for change in journal["changes"]:
        target = regular_path(change["target"])
        level = runtime.config.get("level_name", "world")
        allowed = {runtime.server / "mods", runtime.client, runtime.server / level / "datapacks"}
        if target.parent not in allowed or not re.fullmatch(r"backup/[0-9]+", change["backup"]):
            raise DeployError("Transaction contains an unmanaged target or backup path")
        current = digest(target) if target.exists() else None
        if current not in {change["before"], change["after"]}:
            raise DeployError("Rollback conflict; a tracked file changed after deployment: " + str(target))
        if change["before"] is not None:
            backup = regular_path(directory / change["backup"])
            if not backup.is_file() or digest(backup) != change["before"]:
                raise DeployError("Backup verification failed")
    for change in reversed(journal["changes"]):
        target = regular_path(change["target"])
        if change["before"] is None:
            target.unlink(missing_ok=True)
        else:
            copy_atomic(directory / change["backup"], target)


def deploy(runtime, manifest, base, stop_client=False):
    with runtime.lock():
        for existing in (runtime.state / "transactions").glob("*/journal.json"):
            if read_json(existing).get("status") not in {"deployed", "rolled_back"}:
                raise DeployError("An unfinished transaction must be recovered before another deployment")
        changes = build_plan(runtime, manifest, base)
        was_running = bool(runtime.owned())
        client_stopped = runtime.stop_client(allowed=stop_client)
        transaction = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12]
        directory = runtime.state / "transactions" / transaction
        directory.mkdir(parents=True, mode=0o700)
        journal = {"schema_version": 1, "id": transaction, "job_id": manifest["job_id"], "server_root": str(runtime.server), "client_mods": str(runtime.client), "status": "preparing", "was_running": was_running, "client_stopped": client_stopped, "changes": changes}
        for index, change in enumerate(changes):
            target = Path(change["target"])
            change["before"] = digest(target) if target.exists() else None
            change["backup"] = "backup/" + str(index)
            if target.exists():
                copy_atomic(target, directory / change["backup"])
            # Snapshot validated inputs, so a concurrent rebuild cannot change
            # what gets installed between the preflight and the actual copy.
            if change["source"]:
                snapshot = directory / "artifacts" / str(index)
                copy_atomic(change["source"], snapshot)
                if digest(snapshot) != change["after"]:
                    raise DeployError("Artifact changed while preparing deployment")
                change["source"] = str(snapshot)
        save_journal(directory, journal)
        runtime.stop()  # A failed stop cannot lead to artifact mutation.
        startup_attempted = False
        startup_ready = False
        try:
            snapshot_world(runtime, directory, journal)
            journal["status"] = "installing"
            save_journal(directory, journal)
            # Refuse a change that happened while the server was shutting down.
            for change in changes:
                target = Path(change["target"])
                if (digest(target) if target.exists() else None) != change["before"]:
                    raise DeployError("Artifact changed during shutdown")
            for change in changes:
                if change["source"]:
                    copy_atomic(change["source"], change["target"])
                else:
                    Path(change["target"]).unlink()
            journal["status"] = "starting"
            save_journal(directory, journal)
            startup_attempted = True
            journal["server"] = runtime.start()
            startup_ready = True
            journal["status"] = "deployed"
            save_journal(directory, journal)
            return journal
        except Exception:
            journal["status"] = "recovery_required"
            save_journal(directory, journal)
            try:
                runtime.stop()
                restore_files(directory, journal, runtime)
                if startup_attempted and not startup_ready:
                    # Only automatic recovery from this failed startup may undo
                    # its world changes. Normal rollback never rewinds later play.
                    restore_world(runtime, directory, journal, world_inventory(runtime)[2])
                if was_running:
                    runtime.start()
                journal["status"] = "rolled_back"
                save_journal(directory, journal)
            except Exception:
                # Preserve the journal and original error for operator recovery.
                raise DeployError("Deploy failed and recovery needs attention; use the transaction journal") from None
            raise DeployError("Deploy failed; previous tracked files restored") from None


def rollback(runtime, transaction, restore_world_fingerprint=None, stop_client=False):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}-[0-9a-f]{12}", transaction):
        raise DeployError("Invalid transaction id")
    with runtime.lock():
        directory = runtime.state / "transactions" / transaction
        journal = read_json(regular_path(directory / "journal.json"))
        if journal.get("server_root") != str(runtime.server) or journal.get("client_mods") != str(runtime.client):
            raise DeployError("Transaction belongs to a different runtime")
        if journal.get("status") == "rolled_back":
            return journal
        if restore_world_fingerprint and runtime.running():
            raise DeployError("Stop the server and inspect world-status before explicitly restoring a world")
        if restore_world_fingerprint and world_inventory(runtime)[2] != restore_world_fingerprint:
            raise DeployError("World changed since the requested restore fingerprint")
        # Validate before stopping; restore_files repeats validation after stop.
        for change in journal["changes"]:
            target = regular_path(change["target"])
            if (digest(target) if target.exists() else None) not in {change["before"], change["after"]}:
                raise DeployError("Rollback conflict: " + str(target))
        runtime.stop_client(allowed=stop_client)
        runtime.stop()
        journal["status"] = "recovery_required"
        save_journal(directory, journal)
        restore_files(directory, journal, runtime)
        if restore_world_fingerprint:
            restore_world(runtime, directory, journal, restore_world_fingerprint)
        if journal["was_running"]:
            journal["server"] = runtime.start()
        journal["status"] = "rolled_back"
        save_journal(directory, journal)
        return journal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("plan", "deploy"):
        command = sub.add_parser(action)
        command.add_argument("--manifest", required=True, type=Path)
        command.add_argument("--stop-client", action="store_true")
    command = sub.add_parser("rollback")
    command.add_argument("--transaction", required=True)
    command.add_argument("--stop-client", action="store_true")
    command.add_argument("--restore-world-fingerprint")
    sub.add_parser("adopt").add_argument("--pid", required=True, type=int)
    for action in ("status", "start", "stop", "history", "world-status"):
        sub.add_parser(action)
    args = parser.parse_args()
    try:
        runtime = Runtime(read_json(args.config))
        if args.action == "plan":
            result = build_plan(runtime, read_json(args.manifest), args.manifest.parent)
        elif args.action == "deploy":
            result = deploy(runtime, read_json(args.manifest), args.manifest.parent, args.stop_client)
        elif args.action == "rollback":
            result = rollback(runtime, args.transaction, args.restore_world_fingerprint, args.stop_client)
        elif args.action == "history":
            result = [{key: j.get(key) for key in ("id", "job_id", "status")} for p in sorted((runtime.state / "transactions").glob("*/journal.json")) for j in [read_json(p)]]
        else:
            with runtime.lock():
                if args.action == "adopt":
                    result = runtime.adopt(args.pid)
                elif args.action == "start":
                    result = runtime.start()
                elif args.action == "stop":
                    runtime.stop()
                    result = {"running": False}
                elif args.action == "world-status":
                    if runtime.running():
                        raise DeployError("Stop the server before computing a consistent world fingerprint")
                    result = {"world_sha256": world_inventory(runtime)[2]}
                else:
                    result = {"process": runtime.owned()}
        print(json.dumps(result, indent=2))
        return 0
    except (DeployError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
