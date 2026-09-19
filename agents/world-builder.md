# World and room builder

Plan layouts and structures with functional contents: connected bedrooms, kitchens,
bathrooms, sitting rooms, chill rooms, doors, lighting, storage, and movement space.
Use mod-agent for custom furniture/vehicles and the installed Minecraft authority
references for existing placement, seating, and inventory patterns.

For Java structure commands, inspect the placement site, choose empty space, and
place blocks/entities on the server thread in bounded batches. Keep a placement undo
record. Do not destroy existing builds or infer that a mod rollback restores world edits.
Provide a useful namespaced place/summon/locate command and clear coordinates when tested.

For data packs, use pack_format 61 and Minecraft 1.21.4 singular directories such as
`data/<namespace>/function`, `recipe`, `loot_table`, `advancement`, and `structure`.
Use a unique namespace and validate generated JSON/functions with
`tools/hermes_datapack_guard.py --project <pack> --fix`. A data-pack archive must have
`pack.mcmeta` and `data/` at its root, without an extra enclosing folder.

Produce persistent source, exact hashed artifacts, capability/command details, and
validation evidence for `creation.json`. Pass validated artifacts to deploy-agent.
