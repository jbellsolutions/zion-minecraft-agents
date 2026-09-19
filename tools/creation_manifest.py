"""Versioned creation contract used by providers, jobs and deployment tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

try:
    from .asset_validation import resource_parts, validate_png, validate_resource_tree
except ImportError:
    from asset_validation import resource_parts, validate_png, validate_resource_tree

TARGET = {"minecraft": "1.21.4", "loader": "forge", "forge": "54.1.0", "java": 21}
REQUIRED_EVIDENCE = {"compile", "server_start", "client_render", "client_join", "gameplay", "restart", "artifact_parity"}
CAPABILITY_KINDS = {"item", "block", "entity", "room", "structure"}
ASSET_KINDS = {"inventory_icon", "model", "texture", "thumbnail", "item_definition", "blockstate"}
ACTIONS = {"give", "spawn", "place", "find", "help"}
SLUG = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confined_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or "\\" in name:
        raise ValueError("artifact paths must be nonempty relative paths")
    if any(part in (".", "..") for part in Path(name).parts):
        raise ValueError("artifact paths cannot traverse directories")
    resolved = (root / name).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("artifact path leaves the creation directory") from exc
    return resolved


def read_manifest(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("creation manifest must be a JSON object")
    return data


def archive_issues(path: Path, kind: str) -> list[str]:
    issues = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            names = [entry.filename for entry in members]
            if len(names) != len(set(names)):
                return [f"{path}: duplicate archive entries"]
            if sum(entry.file_size for entry in members) > 128 * 1024 * 1024 or len(members) > 20000:
                return [f"{path}: archive exceeds inspection limits"]
            with tempfile.TemporaryDirectory(prefix="zion-archive-check-") as temporary:
                root = Path(temporary)
                for entry in members:
                    destination = confined_path(root, entry.filename.rstrip("/"))
                    if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("archive symlinks are not supported")
                    if entry.is_dir():
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(entry))
                metadata = root / "pack.mcmeta"
                pack = read_manifest(metadata).get("pack", {}) if metadata.is_file() else {}
                expected = 46 if kind == "jar" else 61
                if not isinstance(pack, dict) or pack.get("pack_format") != expected:
                    issues.append(f"{path}: archive root pack.mcmeta must use pack_format {expected}")
                if kind == "jar":
                    if not (root / "META-INF/mods.toml").is_file():
                        issues.append(f"{path}: missing Forge META-INF/mods.toml")
                    if not any(name.endswith(".class") for name in names):
                        issues.append(f"{path}: JAR contains no compiled classes")
                    issues.extend(validate_resource_tree(root))
                    if (root / "data").is_dir():
                        try:
                            from .hermes_datapack_guard import validate_functions, validate_json_files, validate_namespaces
                        except ImportError:
                            from hermes_datapack_guard import validate_functions, validate_json_files, validate_namespaces
                        validate_namespaces(root, issues)
                        validate_json_files(root, issues)
                        validate_functions(root, issues)
                else:
                    try:
                        from .hermes_datapack_guard import validate
                    except ImportError:
                        from hermes_datapack_guard import validate
                    issues.extend(validate(root, fix=False)[0])
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        issues.append(f"{path}: cannot validate archive: {exc}")
    return issues


def missing_evidence(data: dict) -> list[str]:
    records = data.get("evidence", [])
    hashes = {artifact["sha256"] for artifact in data.get("artifacts", []) if isinstance(artifact, dict) and isinstance(artifact.get("sha256"), str)}
    passed = {(record.get("check"), record.get("artifact_sha256")) for record in records
              if isinstance(record, dict) and record.get("status") == "passed"}
    return sorted(check + (f" ({digest[:12]})" if len(hashes) > 1 else "")
                  for digest in hashes for check in REQUIRED_EVIDENCE if (check, digest) not in passed)


def validate_manifest(path: Path, require_evidence: bool = False) -> list[str]:
    path = Path(path).resolve()
    root, issues = path.parent, []
    try:
        data = read_manifest(path)
    except (OSError, ValueError) as exc:
        return [f"{path}: {exc}"]
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        issues.append("schema_version must be 1")
    if not isinstance(data.get("id"), str) or not SLUG.fullmatch(data["id"]):
        issues.append("id must be a lowercase creation identifier")
    for field in ("name", "request"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            issues.append(f"{field} must be a nonempty string")
    if data.get("target") != TARGET:
        issues.append(f"target must match {TARGET}")
    for field in ("capabilities", "assets", "commands", "artifacts", "evidence"):
        if not isinstance(data.get(field), list):
            issues.append(f"{field} must be an array")
    if issues:
        return issues

    fields = {
        "capabilities": ("id", "kind", "description"),
        "assets": ("path", "kind", "sha256"),
        "commands": ("literal", "capability_id", "action"),
        "artifacts": ("path", "kind", "sha256"),
        "evidence": ("check", "status"),
    }
    for collection, required in fields.items():
        for entry in data[collection]:
            if not isinstance(entry, dict):
                issues.append(f"{collection} entries must be objects")
                continue
            for field in required:
                if not isinstance(entry.get(field), str) or not entry[field]:
                    issues.append(f"{collection}.{field} must be a nonempty string")
            for field in ("capability_id", "registry_id", "path", "sha256", "artifact_sha256"):
                if field in entry and not isinstance(entry[field], str):
                    issues.append(f"{collection}.{field} must be a string")
            if "requires_geometry" in entry and not isinstance(entry["requires_geometry"], bool):
                issues.append(f"{collection}.requires_geometry must be a boolean")
    if issues:
        return sorted(set(issues))

    capabilities = {}
    for entry in data["capabilities"]:
        if not isinstance(entry, dict):
            issues.append("capability must be an object")
            continue
        ident = entry.get("id")
        if not isinstance(ident, str) or not SLUG.fullmatch(ident) or ident in capabilities:
            issues.append(f"invalid or duplicate capability id: {ident!r}")
            continue
        capabilities[ident] = entry
        if entry.get("kind") not in CAPABILITY_KINDS or not isinstance(entry.get("description"), str) or not entry["description"].strip():
            issues.append(f"{ident}: capability needs a supported kind and description")
        if entry.get("kind") in ("item", "block", "entity"):
            try:
                resource_parts(entry.get("registry_id"))
            except ValueError:
                issues.append(f"{ident}: physical content requires registry_id")
    if not capabilities:
        issues.append("creation must contain at least one capability")

    command_ids, literals = set(), set()
    for entry in data["commands"]:
        if not isinstance(entry, dict):
            issues.append("command must be an object")
            continue
        literal = entry.get("literal", "")
        if not isinstance(literal, str) or not re.fullmatch(r"/zion [a-z0-9_ <>:.-]+", literal) or literal in literals:
            issues.append(f"invalid or duplicate command: {literal!r}")
        literals.add(literal if isinstance(literal, str) else "")
        if entry.get("capability_id") not in capabilities or entry.get("action") not in ACTIONS:
            issues.append(f"{literal}: command must reference a capability and supported action")
        else:
            command_ids.add(entry["capability_id"])
    for ident in capabilities.keys() - command_ids:
        issues.append(f"{ident}: missing discoverable slash command")

    def checked_file(entry, label):
        try:
            target = confined_path(root, entry.get("path"))
            expected = entry.get("sha256")
            if not isinstance(expected, str) or not SHA256.fullmatch(expected):
                raise ValueError("requires lowercase sha256")
            if not target.is_file() or file_sha256(target) != expected:
                raise ValueError("missing file or SHA-256 mismatch")
            return target
        except (OSError, ValueError) as exc:
            issues.append(f"{label}: {exc}")
            return None

    assets_by_capability = {ident: [] for ident in capabilities}
    thumbnails = 0
    for entry in data["assets"]:
        if not isinstance(entry, dict):
            issues.append("asset must be an object")
            continue
        if entry.get("kind") not in ASSET_KINDS:
            issues.append(f"unsupported asset kind: {entry.get('kind')!r}")
        ident = entry.get("capability_id")
        if ident is not None and ident not in capabilities:
            issues.append(f"asset references unknown capability: {ident!r}")
        elif ident in assets_by_capability:
            assets_by_capability[ident].append(entry)
        target = checked_file(entry, "asset")
        if target and entry.get("kind") in ("inventory_icon", "thumbnail", "texture"):
            issues.extend(validate_png(target, inventory=entry["kind"] == "inventory_icon", release=True))
        if target and entry.get("kind") == "thumbnail":
            thumbnails += 1
    if not thumbnails:
        issues.append("creation requires a library thumbnail")
    for ident, capability in capabilities.items():
        kinds = {entry.get("kind") for entry in assets_by_capability[ident]}
        if capability.get("kind") in ("item", "entity") and "inventory_icon" not in kinds:
            issues.append(f"{ident}: missing recognizable inventory icon")
        if capability.get("kind") == "block" and "inventory_icon" not in kinds and not {"item_definition", "model"} <= kinds:
            issues.append(f"{ident}: block requires an icon or its modeled inventory representation")
        if capability.get("requires_geometry") and capability.get("kind") == "block":
            models = [entry for entry in assets_by_capability[ident] if entry.get("kind") == "model"]
            shaped = False
            for entry in models:
                try:
                    model = read_manifest(confined_path(root, entry.get("path")))
                    elements = model.get("elements")
                    if isinstance(elements, list) and elements:
                        shaped |= not (len(elements) == 1 and isinstance(elements[0], dict) and
                                       elements[0].get("from") == [0, 0, 0] and elements[0].get("to") == [16, 16, 16])
                except (OSError, ValueError):
                    pass
            if not shaped:
                issues.append(f"{ident}: furniture requires nonempty shaped geometry, not cube_all")

    artifact_hashes, artifact_paths, packaged_assets = set(), set(), {}
    if not data["artifacts"]:
        issues.append("creation requires at least one built artifact")
    for entry in data["artifacts"]:
        if not isinstance(entry, dict):
            issues.append("artifact must be an object")
            continue
        target = checked_file(entry, "artifact")
        if entry["path"] in artifact_paths or entry["sha256"] in artifact_hashes:
            issues.append("artifacts must have unique paths and content hashes")
        artifact_paths.add(entry["path"])
        if entry.get("kind") not in ("jar", "datapack"):
            issues.append("artifact kind must be jar or datapack")
        elif target:
            artifact_hashes.add(entry["sha256"])
            archive_errors = archive_issues(target, entry["kind"])
            issues.extend(archive_errors)
            if entry["kind"] == "jar" and not archive_errors:
                try:
                    with zipfile.ZipFile(target) as archive:
                        for info in archive.infolist():
                            if info.filename.startswith("assets/") and not info.is_dir():
                                digest = hashlib.sha256(archive.read(info)).hexdigest()
                                if info.filename in packaged_assets and packaged_assets[info.filename] != digest:
                                    issues.append(f"conflicting packaged resource: {info.filename}")
                                packaged_assets[info.filename] = digest
                except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
                    pass  # archive_issues reports the readable failure above.
    for ident, capability in capabilities.items():
        if capability.get("kind") not in ("item", "entity", "block"):
            continue
        try:
            namespace, name = resource_parts(capability.get("registry_id"))
        except ValueError:
            continue
        required = [f"assets/{namespace}/items/{name}.json"]
        if capability["kind"] == "block":
            required.append(f"assets/{namespace}/blockstates/{name}.json")
        for resource in required:
            if resource not in packaged_assets:
                issues.append(f"{ident}: built JAR is missing {resource}")
    for entry in data["assets"]:
        if entry["kind"] == "thumbnail":
            continue
        parts = Path(entry["path"]).parts
        if "assets" not in parts:
            issues.append(f"{entry['path']}: release asset path must identify its assets/ resource location")
            continue
        resource = "/".join(parts[parts.index("assets"):])
        if packaged_assets.get(resource) != entry["sha256"]:
            issues.append(f"{resource}: declared asset does not match a packaged JAR resource")
    seen_evidence = set()
    for entry in data["evidence"]:
        if not isinstance(entry, dict) or entry.get("check") not in REQUIRED_EVIDENCE:
            issues.append("unsupported evidence check")
            continue
        check = entry["check"]
        identity = (check, entry.get("artifact_sha256"))
        if identity in seen_evidence:
            issues.append(f"duplicate evidence check for artifact: {check}")
        seen_evidence.add(identity)
        if entry.get("status") not in ("passed", "failed", "pending"):
            issues.append(f"{check}: unsupported evidence status")
        elif entry["status"] == "failed":
            issues.append(f"{check}: verification failed")
        elif entry["status"] == "passed":
            target = checked_file(entry, f"{check} evidence")
            if target and not target.stat().st_size:
                issues.append(f"{check}: evidence report is empty")
            if entry.get("artifact_sha256") not in artifact_hashes:
                issues.append(f"{check}: evidence does not identify a current artifact")
    if require_evidence:
        for check in missing_evidence(data):
            issues.append(f"missing passed evidence: {check}")
    return sorted(set(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-evidence", action="store_true")
    args = parser.parse_args()
    issues = validate_manifest(args.manifest, args.require_evidence)
    print(json.dumps({"valid": not issues, "issues": issues}, indent=2))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
