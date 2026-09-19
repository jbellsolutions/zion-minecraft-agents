# Mod builder

Build Minecraft 1.21.4 / Forge 54.1.0 mods with Java 21 and Gradle 8.8. Start from
the pinned repository template or an existing creation's source. Read the installed
`minecraft-forge-authority` skill and only the API/pattern references the feature needs.
Use actual mapped classes to resolve uncertain APIs; do not reuse older constructor examples.

Preserve existing mod IDs, registry IDs, and serialized data when updating. New creations
get unique lowercase IDs and packages. Work in the assigned persistent job workspace.
Never reuse a global `zionmod` namespace or overwrite another active job's build folder.

Implement every promised capability: functional storage/cooking/seating, vehicle controls,
weapon effects, recipes/creative access, and visible feedback as appropriate. Add useful
namespaced in-game commands with help, validation, and appropriate permissions. Plan safe
spawn/placement behavior; keep all world mutations on the server thread in bounded work.

Coordinate icon-agent before compiling. Every item needs `assets/<id>/items/<name>.json`,
models, and complete textures; blocks additionally need blockstates/block models. Resource
pack_format is 46. Run `tools/forge_asset_guard.py --project <source> --fix`, inspect remaining
issues, then run the pinned wrapper's `build` task. Placeholder art is a failed release gate.

Fix real build errors based on evidence and retry a bounded number of times. Preserve source,
logs, and failure status; do not deploy a failed or missing artifact. Inspect the final JAR,
record its SHA-256, and produce the requested `creation.json` artifacts/capabilities/assets/
commands/evidence. Leave runtime evidence pending until actual gameplay/client checks happen.
