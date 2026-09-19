---
name: hermes-minecraft-superbuilder
description: Implement complex Minecraft 1.21.4 Forge features with complete behavior, inventory artwork, slash commands, build evidence, and safe deployment. Use for multi-part creations and upgrades to existing Zion mods.
---

# Complete Minecraft creations

Read the `zion` skill for command routing and durable jobs. Keep the installed
`minecraft-forge-authority` skill as the source of learned Forge patterns. Prefer
relevant references for seats, rideable entities, block inventories, shaders, item
definitions, and structure commands over unverified Java examples.

Translate a broad request into explicit capabilities with observable behavior:

- **Kitchen:** fridge stores items, stove/oven cooks, grill has a cooking interaction,
  clear doors and counters, lighting, and a way to find/place each object.
- **Bedroom/sitting/chill room:** usable seats or beds, sensible proportions, storage,
  doors, bookshelves, lighting, and a distinct visual style.
- **Vehicle:** mounting, movement/steering, collision, dismounting, persistence, and
  a summon command. A decorative model does not satisfy a rideable vehicle request.
- **Sword/tool:** visible silhouette, shine/highlights, appropriate hand-held model,
  usable behavior, recipe or creative access, and a give/test command.
- **House:** connected layout, usable rooms, bounded placement, site inspection,
  and a placement undo record. Deployment rollback does not undo construction.

Use unique namespaces for new creations and preserve IDs for updates. Handle normal
creative ambiguity autonomously and make the chosen interpretation visible in the
manifest. State any feature that remains incomplete rather than relabeling it complete.

The target is Minecraft 1.21.4 / Forge 54.1.0 / Java 21 / Gradle 8.8. Resource-pack
format is 46; data-pack format is 61. Every item needs its 1.21.4 client item definition.
Run source guards, compile, inspect the final archive, and capture runtime evidence
separately. Icons and meaningful slash commands are part of the creation before deploy.
