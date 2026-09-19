"""Shared, dependency-free PNG and Minecraft resource-graph validation."""
from __future__ import annotations

import json
import math
import re
import struct
import zlib
from pathlib import Path

RESOURCE_ID = re.compile(r"^(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+$")


def decode_png(data: bytes) -> dict:
    """Decode non-interlaced 8-bit PNGs, including palette images and all filters.

    CRC, compressed stream, scanline length and palette indices are checked; a
    plausible IHDR header alone is never accepted as an image.
    """
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, chunks, compressed = 8, [], bytearray()
    palette, transparency, header = b"", b"", None
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + size
        if end > len(data):
            raise ValueError("truncated PNG data")
        payload = data[pos + 8:pos + 8 + size]
        crc = struct.unpack_from(">I", data, pos + 8 + size)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("PNG checksum mismatch")
        chunks.append(kind)
        if kind == b"IHDR":
            if header is not None or size != 13 or len(chunks) != 1:
                raise ValueError("invalid PNG header")
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"PLTE":
            if not size or size % 3 or size > 768:
                raise ValueError("invalid PNG palette")
            palette = payload
        elif kind == b"tRNS":
            transparency = payload
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if size or end != len(data):
                raise ValueError("invalid PNG ending")
            pos = end
            break
        pos = end
    if not header or not chunks or chunks[-1] != b"IEND" or not compressed:
        raise ValueError("incomplete PNG")
    width, height, depth, color, compression, filtering, interlace = header
    if not (0 < width <= 1024 and 0 < height <= 1024):
        raise ValueError("PNG dimensions must be between 1 and 1024")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if depth != 8 or channels is None or compression or filtering or interlace:
        raise ValueError("export PNG as non-interlaced 8-bit RGB, RGBA, grayscale or indexed color")
    if color == 3 and not palette:
        raise ValueError("indexed PNG has no palette")
    stride = width * channels
    expected = height * (stride + 1)
    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(bytes(compressed), expected + 1)
    except zlib.error as exc:
        raise ValueError("invalid compressed PNG pixels") from exc
    if len(raw) != expected or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError("PNG pixel data length mismatch")
    previous = bytearray(stride)
    alpha_min, alpha_max, colors = 255, 0, set()
    for y in range(height):
        offset = y * (stride + 1)
        filter_type = raw[offset]
        if filter_type > 4:
            raise ValueError("invalid PNG scanline filter")
        row = bytearray(raw[offset + 1:offset + stride + 1])
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            above = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            predictor = 0
            if filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                p = left + above - upper_left
                distances = (abs(p - left), abs(p - above), abs(p - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            row[i] = (row[i] + predictor) & 255
        for x in range(width):
            pixel = tuple(row[x * channels:(x + 1) * channels])
            alpha = 255
            if color in (4, 6):
                alpha = pixel[-1]
            elif color == 3:
                index = pixel[0]
                if index * 3 + 2 >= len(palette):
                    raise ValueError("PNG palette index out of range")
                alpha = transparency[index] if index < len(transparency) else 255
                pixel = tuple(palette[index * 3:index * 3 + 3])
            elif color == 0 and len(transparency) == 2:
                alpha = 0 if pixel[0] == struct.unpack(">H", transparency)[0] else 255
            elif color == 2 and len(transparency) == 6:
                alpha = 0 if pixel == struct.unpack(">HHH", transparency) else 255
            alpha_min, alpha_max = min(alpha_min, alpha), max(alpha_max, alpha)
            if alpha and len(colors) < 256:
                colors.add(pixel)
        previous = row
    return {"width": width, "height": height, "transparent": alpha_min == 0,
            "visible": alpha_max > 0, "visible_colors": len(colors)}


def validate_png(path: Path, *, inventory: bool = False, release: bool = False) -> list[str]:
    try:
        image = decode_png(path.read_bytes())
    except (OSError, ValueError) as exc:
        return [f"{path}: {exc}"]
    issues = []
    width, height = image["width"], image["height"]
    if width != height or width & (width - 1):
        issues.append(f"{path}: texture must be square and power-of-two sized")
    if inventory:
        if release and (width, height) != (64, 64):
            issues.append(f"{path}: release inventory icons must be 64x64")
        if not image["transparent"] or not image["visible"] or image["visible_colors"] < 2:
            issues.append(f"{path}: inventory icon needs a visible, colored silhouette on a transparent background; placeholders are not release artwork")
    return issues


def resource_parts(reference: str) -> tuple[str, str]:
    if not isinstance(reference, str) or not RESOURCE_ID.fullmatch(reference):
        raise ValueError(f"invalid resource reference {reference!r}")
    namespace, path = reference.split(":", 1) if ":" in reference else ("minecraft", reference)
    if path.startswith("/") or any(part in (".", "..", "") for part in path.split("/")):
        raise ValueError(f"unsafe resource reference {reference!r}")
    return namespace, path


def validate_resource_tree(resources: Path) -> list[str]:
    """Validate custom references; vanilla references remain owned by Minecraft."""
    assets = resources / "assets"
    issues, parsed, completed = [], {}, {}

    def read(path):
        if path in parsed:
            return parsed[path]
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("must contain a JSON object")
        except (OSError, ValueError) as exc:
            issues.append(f"{path}: {exc}")
            value = {}
        parsed[path] = value
        return value

    def resource(reference, kind):
        try:
            namespace, name = resource_parts(reference)
        except ValueError as exc:
            issues.append(str(exc))
            return None
        if namespace == "minecraft":
            return None
        extension = ".png" if kind == "textures" else ".json"
        path = assets / namespace / kind / (name + extension)
        if not path.is_file():
            issues.append(f"missing referenced {kind}: {reference}")
            return None
        return path

    def model(path, stack=()):
        if path in stack:
            issues.append(f"cyclic model parent: {path}")
            return {}
        if path in completed:
            return completed[path]
        data = read(path)
        textures = {}
        if "parent" in data:
            parent = resource(data["parent"], "models")
            if parent:
                textures.update(model(parent, stack + (path,)))
        elif not isinstance(data.get("elements"), list) or not data["elements"]:
            issues.append(f"{path}: model requires a parent or nonempty elements")
        own = data.get("textures", {})
        if not isinstance(own, dict):
            issues.append(f"{path}: textures must be an object")
        else:
            textures.update(own)

        def texture(value, seen=()):
            if not isinstance(value, str):
                issues.append(f"{path}: invalid texture reference")
            elif value.startswith("#"):
                key = value[1:]
                if key in seen or key not in textures:
                    issues.append(f"{path}: unresolved or cyclic texture alias {value}")
                else:
                    texture(textures[key], seen + (key,))
            else:
                resource(value, "textures")
        for value in textures.values():
            texture(value)
        if "elements" in data and not isinstance(data["elements"], list):
            issues.append(f"{path}: model elements must be an array")
        for element in data.get("elements", []) if isinstance(data.get("elements", []), list) else []:
            if not isinstance(element, dict) or not isinstance(element.get("faces", {}), dict):
                issues.append(f"{path}: invalid model element")
                continue
            coordinates = (element.get("from"), element.get("to"))
            valid_coordinates = all(isinstance(vector, list) and len(vector) == 3 and
                                    all(type(value) in (int, float) and math.isfinite(value) and -16 <= value <= 32 for value in vector)
                                    for vector in coordinates)
            if not valid_coordinates:
                issues.append(f"{path}: elements need three finite from/to coordinates in [-16, 32]")
            elif any(a > b for a, b in zip(*coordinates)):
                issues.append(f"{path}: element from coordinates exceed to coordinates")
            for face in element.get("faces", {}).values():
                if not isinstance(face, dict) or "texture" not in face:
                    issues.append(f"{path}: model face requires a texture")
                else:
                    texture(face["texture"])
        completed[path] = textures
        return textures

    def walk_models(value):
        if isinstance(value, dict):
            if "model" in value and isinstance(value["model"], str):
                path = resource(value["model"], "models")
                if path:
                    model(path)
            for child in value.values():
                walk_models(child)
        elif isinstance(value, list):
            for child in value:
                walk_models(child)

    for path in sorted(assets.glob("*/models/**/*.json")):
        model(path)
    for path in sorted(assets.glob("*/items/*.json")):
        data = read(path)
        definition = data.get("model")
        if not isinstance(definition, dict) or not isinstance(definition.get("type"), str):
            issues.append(f"{path}: item definition needs a typed model object")
        elif definition.get("type") == "minecraft:model" and not isinstance(definition.get("model"), str):
            issues.append(f"{path}: minecraft:model requires a model resource")
        walk_models(data)
    for path in sorted(assets.glob("*/blockstates/*.json")):
        data = read(path)
        if not ((isinstance(data.get("variants"), dict) and data["variants"]) or
                (isinstance(data.get("multipart"), list) and data["multipart"])):
            issues.append(f"{path}: blockstate needs nonempty variants or multipart")
        walk_models(data)
    for path in sorted(assets.glob("*/textures/**/*.png")):
        issues.extend(validate_png(path, inventory="/textures/item/" in path.as_posix()))
    return sorted(set(issues))
