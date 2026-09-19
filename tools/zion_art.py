#!/usr/bin/env python3
"""Generate and validate transparent inventory art through OpenRouter's Image API."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MODEL = "openai/gpt-image-2.5-sunburst"
API = "https://openrouter.ai/api/v1/images"


def api_key():
    value = os.environ.get("OPENROUTER_API_KEY")
    if value:
        return value
    path = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))) / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "OPENROUTER_API_KEY":
                return value.strip().strip("\"'")
    raise ValueError("OpenRouter image key is not configured")


def normalize(raw):
    from PIL import Image
    with Image.open(io.BytesIO(raw)) as original:
        original.load()
        if original.width > 4096 or original.height > 4096:
            raise ValueError("Image exceeds asset size limit")
        image = original.convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] != 0 or alpha.getextrema()[1] < 128:
        raise ValueError("Icon requires real transparent background and visible artwork")
    bounds = alpha.getbbox()
    if not bounds:
        raise ValueError("Icon is empty")
    image = image.crop(bounds)
    image.thumbnail((56, 56), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    icon.alpha_composite(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    pixels = icon.get_flattened_data() if hasattr(icon, "get_flattened_data") else icon.getdata()
    visible = [pixel for pixel in pixels if pixel[3] > 32]
    if len(visible) < 64 or len({pixel[:3] for pixel in visible}) < 12:
        raise ValueError("Icon lacks a readable detailed silhouette")
    output = io.BytesIO()
    icon.save(output, format="PNG")
    return output.getvalue()


def generate(prompt, destination, opener=urlopen):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Destination exists; choose a new asset filename")
    body = {"model": MODEL, "prompt": prompt +
            " Single recognisable Minecraft inventory icon. Crisp silhouette readable at 64 pixels."
            " True transparent background, no text, no checkerboard or colored square backdrop.",
            "n": 1, "aspect_ratio": "1:1", "quality": "medium",
            "background": "transparent", "output_format": "png"}
    request = Request(API, data=json.dumps(body).encode(),
                      headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"})
    # No automatic retry: ambiguous image timeouts can have a financial side effect.
    with opener(request, timeout=180) as response:
        result = json.load(response)
    record = result["data"][0]
    if record.get("media_type", "image/png") != "image/png":
        raise ValueError("Generator returned a non-PNG asset")
    raw = base64.b64decode(record["b64_json"], validate=True)
    image = normalize(raw)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(image)
    report = {"model": MODEL, "prompt": body["prompt"], "width": 64, "height": 64,
              "sha256": hashlib.sha256(image).hexdigest(), "alpha_validated": True,
              "visual_review": "pending", "usage": result.get("usage", {})}
    destination.with_suffix(".provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        print(json.dumps(generate(args.prompt, args.output)))
    except HTTPError as error:
        print(json.dumps({"status": "failed", "http_status": error.code,
                          "error": "Image provider rejected the request"}), file=sys.stderr)
        return 1
    except Exception as error:
        # Never expose upstream response bodies or credentials in provider logs.
        print(json.dumps({"status": "failed", "error_type": type(error).__name__,
                          "error": "No validated icon was produced"}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
