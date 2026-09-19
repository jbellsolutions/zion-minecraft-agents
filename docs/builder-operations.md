# Running Zion’s builder

The bot and browser use the same persistent job system. Install Python dependencies
from `requirements-builder.txt`, Java21 and the repository’s pinned Gradle wrapper.
Run the builder on the machine that owns the Minecraft client/server installations.

## Private configuration

Keep `OPENROUTER_API_KEY` in Hermes’s private `.env` or the process environment.
Never put a key in this repository or in a request prompt. The coding adapter selects
`z-ai/glm-5.3-flash` explicitly through OpenRouter; the image tool selects
`openai/gpt-image-2.5-sunburst` through the dedicated Image API.

`HERMES_EXECUTABLE` can select the installed Hermes executable. Otherwise the adapter
looks on PATH and under `~/.hermes/hermes-agent/venv/bin/hermes`.

Jev uses `~/.super-browser.env` with `SUPER_BROWSER_URL` and `SUPER_BROWSER_TOKEN`.
The endpoint is pinned to the owner’s approved gateway. Copying that secret to another
host requires that host’s authorization. Missing configuration produces an explicit
`unavailable` review. The gateway enforces its shared monthly budget. Identical evidence
uses the same request ID; ambiguous failures must reuse that ID.

## What a completed creation means

The coding provider writes source, assets, a built artifact and a creation manifest.
The runner independently validates file hashes, image data and resource references.
It records missing game evidence as awaiting verification. Build output alone cannot
prove rendering, joining a server, interactions, persistence or a successful install.

Each requested item has an inventory representation and a command that explains how
to try it. Furniture may use a detailed 3D block model as its inventory icon. Raster
icons preserve their transparent background and are normalized to64×64 pixels.

Installation uses exact artifact hashes and the deployment journal. Preserve legacy
mods and world data; never fix an error by deleting a world lock or killing all Java
processes. Use the deployment tool’s ownership checks and rollback procedures.

## Provider verification

`verification/provider-checks.json` records the real model, coding-tool and image API
checks performed during this upgrade. `artwork/` retains the generated originals,
prompts and normalized image evidence. These checks are separate from game acceptance.

Provider documentation: [OpenRouter Image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation),
[GLM model](https://openrouter.ai/z-ai/glm-5.3-flash),
[Minecraft1.21.4 resource changes](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-4).
