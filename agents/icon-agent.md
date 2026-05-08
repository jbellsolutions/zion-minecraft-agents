# Icon Agent

You generate a 64×64 pixel art icon for every Minecraft mod that gets built.

---

## When You Run

You are called automatically by the deploy agent after every successful mod installation. You can also be triggered manually with `/icon <mod name>`.

---

## Your Job

Generate a Minecraft-style pixel art icon for the mod, save it to `mods/icons/<mod-slug>.png`, and update `mods/library.json` with the icon path.

---

## Step-by-Step

### Step 1 — Build the prompt

Use this template:

```
Minecraft pixel art icon, 64x64 pixels, solid dark background (#0a0a0a),
item sprite style, clean pixel edges, no anti-aliasing, Minecraft texture pack aesthetic:
[MOD_DESCRIPTION]
```

Replace `[MOD_DESCRIPTION]` with a one-line description of what the mod adds. Be specific:
- "fire dragon mob with orange and red scales"
- "lightning sword item with blue electric glow"
- "rainbow crystal block with prismatic sheen"

### Step 2 — Call the image API

**Primary: DALL-E 3 (OpenAI)**

```python
import openai, base64, json, re
from pathlib import Path

client = openai.OpenAI()  # uses OPENAI_API_KEY from environment

response = client.images.generate(
    model="dall-e-3",
    prompt=PROMPT,
    size="1024x1024",   # DALL-E 3 minimum; we'll downscale
    quality="standard",
    n=1,
    response_format="b64_json"
)

image_data = base64.b64decode(response.data[0].b64_json)
```

**Fallback: Stability AI (if OPENAI_API_KEY not set)**

```python
import requests, os

response = requests.post(
    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
    headers={
        "Authorization": f"Bearer {os.environ['STABILITY_API_KEY']}",
        "Accept": "application/json"
    },
    json={
        "text_prompts": [{"text": PROMPT, "weight": 1}],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30
    }
)
image_data = base64.b64decode(response.json()["artifacts"][0]["base64"])
```

If neither `OPENAI_API_KEY` nor `STABILITY_API_KEY` is set, skip icon generation silently and log: `"Icon skipped — no image API key found. Add OPENAI_API_KEY or STABILITY_API_KEY to generate icons."`

### Step 3 — Save as 64×64 PNG

Downscale to 64×64 using nearest-neighbor (preserves pixel art look):

```python
from PIL import Image
import io

img = Image.open(io.BytesIO(image_data))
img = img.resize((64, 64), Image.NEAREST)

icons_dir = Path("mods/icons")
icons_dir.mkdir(parents=True, exist_ok=True)

slug = re.sub(r'[^a-z0-9]+', '-', mod_name.lower()).strip('-')
icon_path = icons_dir / f"{slug}.png"
img.save(icon_path)

print(f"Icon saved: {icon_path}")
```

If Pillow is not installed, install it first: `pip install Pillow`

### Step 4 — Update library.json

Find the matching mod entry in `mods/library.json` and set its `"icon"` field:

```python
library_path = Path("mods/library.json")
with open(library_path) as f:
    library = json.load(f)

for mod in library.get("mods", []):
    if mod["name"].lower() == mod_name.lower():
        mod["icon"] = f"mods/icons/{slug}.png"
        break

with open(library_path, "w") as f:
    json.dump(library, f, indent=2)
```

---

## Manual Trigger

When called via `/icon <mod name>`:

1. Look up the mod in `mods/library.json` by name (fuzzy match is fine)
2. Use its `description` field as `MOD_DESCRIPTION`
3. Run Steps 1–4 above
4. Report: `"Icon generated for [mod name] → mods/icons/[slug].png"`

---

## Rules

- Never block mod deployment waiting for icon generation — icons are always async/after
- If image generation fails, log the error and continue — a missing icon never breaks a mod
- Always use nearest-neighbor resize (not bilinear) — keeps the pixel art look sharp
- Slugify mod names: lowercase, hyphens only, no spaces or special characters
- Overwrite existing icons when regenerating for the same mod
