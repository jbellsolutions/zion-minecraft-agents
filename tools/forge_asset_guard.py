#!/usr/bin/env python3
"""Validate and repair Forge 1.21.4 block/item client assets.

Minecraft 1.21.4 requires item definitions in assets/<modid>/items/*.json.
Older assets/models/item/*.json files alone are not enough.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .asset_validation import decode_png, validate_png, validate_resource_tree
except ImportError:
    from asset_validation import decode_png, validate_png, validate_resource_tree


ROOT_PARTS = ("src", "main", "resources")
PACK_FORMAT_BY_MC = {
    "1.21.4": 46,
}

ITEM_REGISTER_RE = re.compile(r"\bITEMS\s*\.\s*register\s*\(\s*\"([a-z0-9_]+)\"")
BLOCK_REGISTER_RE = re.compile(
    r"\b(?:registerBlock|BLOCKS\s*\.\s*register)\s*\(\s*\"([a-z0-9_]+)\""
)
VALID_ID_RE = re.compile(r"^[a-z0-9_]+$")


def strip_java_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def read_properties(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    if not path.exists():
        return props
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def discover_mod_id(project: Path) -> str:
    props = read_properties(project / "gradle.properties")
    mod_id = props.get("mod_id", "")
    if mod_id and VALID_ID_RE.match(mod_id):
        return mod_id

    mods_toml = project / "src/main/resources/META-INF/mods.toml"
    if mods_toml.exists():
        declared = re.findall(r"\[\[mods\]\][\s\S]*?modId\s*=\s*\"([a-z0-9_]+)\"", mods_toml.read_text(encoding="utf-8"))
        if len(declared) == 1:
            return declared[0]
        if len(declared) > 1:
            raise SystemExit("Multiple mod namespaces: use --mod-id to select the content namespace; no files were changed")

    raise SystemExit("Could not determine mod_id from gradle.properties or mods.toml")


def discover_minecraft_version(project: Path) -> str | None:
    return read_properties(project / "gradle.properties").get("minecraft_version")


def discover_registries(project: Path) -> tuple[set[str], set[str]]:
    blocks: set[str] = set()
    items: set[str] = set()

    java_root = project / "src/main/java"
    if not java_root.exists():
        return blocks, items

    for java_file in java_root.rglob("*.java"):
        text = strip_java_comments(java_file.read_text(encoding="utf-8", errors="ignore"))
        blocks.update(BLOCK_REGISTER_RE.findall(text))
        items.update(ITEM_REGISTER_RE.findall(text))

    items.update(blocks)
    return blocks, items


def title_from_id(registry_name: str) -> str:
    return " ".join(part.capitalize() for part in registry_name.split("_"))


def write_json(path: Path, data: object, fixes: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    fixes.append(f"created {path}")


def ensure_json(path: Path, data: object, fix: bool, issues: list[str], fixes: list[str]) -> None:
    if path.exists():
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeError) as exc:
            issues.append(f"{path} is invalid JSON: {exc}")
        return

    issues.append(f"missing {path}")
    if fix:
        write_json(path, data, fixes)


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        image = decode_png(path.read_bytes())
        return image["width"], image["height"]
    except (OSError, ValueError):
        return None


def ensure_texture(path: Path, mod_id: str, name: str, kind: str, fix: bool, issues: list[str], fixes: list[str]) -> None:
    # Missing art is a build failure. Metadata repair must never silently replace
    # requested artwork with an opaque colored square.
    if not path.exists():
        issues.append(f"missing artwork {path}; create a recognizable texture before building")
        return
    issues.extend(validate_png(path, inventory=kind == "item"))


def ensure_lang(resources: Path, mod_id: str, blocks: set[str], items: set[str], fix: bool, issues: list[str], fixes: list[str]) -> None:
    path = resources / "assets" / mod_id / "lang" / "en_us.json"
    data: dict[str, str] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = {str(k): str(v) for k, v in loaded.items()}
            else:
                issues.append(f"{path} must contain a JSON object")
                return
        except (json.JSONDecodeError, OSError, UnicodeError) as exc:
            issues.append(f"{path} is invalid JSON: {exc}")
            return

    changed = False
    for block in sorted(blocks):
        key = f"block.{mod_id}.{block}"
        if key not in data:
            data[key] = title_from_id(block)
            changed = True
    for item in sorted(items - blocks):
        key = f"item.{mod_id}.{item}"
        if key not in data:
            data[key] = title_from_id(item)
            changed = True
    tab_key = f"itemGroup.{mod_id}"
    if tab_key not in data:
        data[tab_key] = f"{title_from_id(mod_id)} Items"
        changed = True

    if changed:
        issues.append(f"missing language keys in {path}")
        if fix:
            write_json(path, dict(sorted(data.items())), fixes)


def ensure_pack_format(project: Path, fix: bool, issues: list[str], fixes: list[str]) -> None:
    version = discover_minecraft_version(project)
    expected = PACK_FORMAT_BY_MC.get(version or "")
    if expected is None:
        issues.append(f"unsupported or missing minecraft_version: {version!r}; expected 1.21.4")
        return

    path = project / "src/main/resources/pack.mcmeta"
    if not path.exists():
        issues.append(f"missing {path}")
        if fix:
            write_json(path, {"pack": {"pack_format": expected, "description": "Mod resources"}}, fixes)
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError) as exc:
        issues.append(f"{path} is invalid JSON: {exc}")
        return

    pack = data.get("pack") if isinstance(data, dict) else None
    if not isinstance(pack, dict):
        issues.append(f"{path} pack must be a JSON object")
        return
    current = pack.get("pack_format")
    if current != expected:
        issues.append(f"{path} pack_format should be {expected} for Minecraft {version}, got {current}")
        if fix and isinstance(data, dict):
            data.setdefault("pack", {})["pack_format"] = expected
            write_json(path, data, fixes)


def validate(project: Path, fix: bool, mod_id: str | None = None) -> tuple[list[str], list[str]]:
    project = project.resolve()
    mod_id = mod_id or discover_mod_id(project)
    if not VALID_ID_RE.fullmatch(mod_id):
        return ["mod_id must be a lowercase resource namespace"], []
    resources = project / "/".join(ROOT_PARTS)
    assets = resources / "assets" / mod_id
    blocks, items = discover_registries(project)

    issues: list[str] = []
    fixes: list[str] = []

    if not blocks and not items:
        issues.append("no registered blocks or items were found in src/main/java")

    ensure_pack_format(project, fix, issues, fixes)

    for block in sorted(blocks):
        ensure_json(
            assets / "blockstates" / f"{block}.json",
            {"variants": {"": {"model": f"{mod_id}:block/{block}"}}},
            fix,
            issues,
            fixes,
        )
        ensure_json(
            assets / "models" / "block" / f"{block}.json",
            {"parent": "minecraft:block/cube_all", "textures": {"all": f"{mod_id}:block/{block}"}},
            fix,
            issues,
            fixes,
        )
        ensure_json(
            assets / "models" / "item" / f"{block}.json",
            {"parent": f"{mod_id}:block/{block}"},
            fix,
            issues,
            fixes,
        )
        ensure_json(
            assets / "items" / f"{block}.json",
            {"model": {"type": "minecraft:model", "model": f"{mod_id}:block/{block}"}},
            fix,
            issues,
            fixes,
        )

    for item in sorted(items - blocks):
        ensure_json(
            assets / "models" / "item" / f"{item}.json",
            {"parent": "minecraft:item/generated", "textures": {"layer0": f"{mod_id}:item/{item}"}},
            fix,
            issues,
            fixes,
        )
        ensure_json(
            assets / "items" / f"{item}.json",
            {"model": {"type": "minecraft:model", "model": f"{mod_id}:item/{item}"}},
            fix,
            issues,
            fixes,
        )

    ensure_lang(resources, mod_id, blocks, items, fix, issues, fixes)
    issues.extend(validate_resource_tree(resources))

    if fix and fixes:
        issues, fixes_after = validate(project, fix=False, mod_id=mod_id)
        fixes.extend(fixes_after)

    return issues, fixes


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Forge 1.21.4 block/item assets.")
    parser.add_argument("--project", default=".", help="Forge project root")
    parser.add_argument("--mod-id", help="explicit content namespace for a multi-mod source project")
    parser.add_argument("--fix", action="store_true", help="repair missing JSON metadata only; artwork is never fabricated")
    args = parser.parse_args()

    issues, fixes = validate(Path(args.project), args.fix, args.mod_id)
    for fix in fixes:
        print(f"FIXED: {fix}")

    if issues:
        for issue in issues:
            print(f"ISSUE: {issue}", file=sys.stderr)
        return 1

    print("Forge asset guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
