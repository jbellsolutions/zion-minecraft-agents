---
name: zion
version: 1.0.0
description: |
  Zion's Minecraft Mod Builder. Routes natural language requests from a 5-year-old
  through the agent pipeline to build and deploy Minecraft mods automatically.
  Use when asked to build any Minecraft content: mobs, items, blocks, biomes,
  quests, or anything else Zion wants in his world.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - TodoWrite
---

# /zion — Minecraft Mod Builder

Turns Zion's plain English request into an installed Minecraft mod with no manual steps.

## Iron Law

**THE SERVER MUST BE IN A PLAYABLE STATE WHEN THIS SKILL FINISHES.** If the mod fails to build, the server still restarts clean. If the deploy fails, the backup is restored. Zion must always be able to join and play.

Usually do not ask Zion questions. Ask one short question only when the build is blocked by safety,
destructive world changes, incompatible choices, or an unknown target mod. Never leave a half-deployed
state. Never skip the backup. Never skip the restart.

---

## Phase 1: Parse Request

Read the request. Determine which agents are needed:

| Request Type | Agent(s) |
|-------------|---------|
| Mob, creature, boss, animal | mod-agent |
| Item, weapon, tool, armor, food | mod-agent |
| Custom block | mod-agent |
| New biome, structure, dungeon | world-builder |
| Quest, NPC, dialogue, story, book | lore-agent |
| Multiple types | Multiple agents in parallel |

If the request is ambiguous, pick the most fun interpretation. A "fire dragon" is a mob with fire particles, fire damage, and drops. No clarification needed.

Choose a build mode:
- **Quick Mod**: one item, block, command, or small behavior.
- **Feature Mod**: custom item/block/entity with recipes, drops, assets, and tests.
- **Adventure Pack**: mod + worldgen/structure + quest/story content.
- **Update Pass**: inspect an existing mod and add/change behavior without breaking it.
- **Repair Pass**: diagnose logs/build output, fix, rebuild, and redeploy safely.

---

## Phase 2: Build

Run the appropriate agent(s) from `agents/`:
- `agents/mod-agent.md` — Java Forge mod (produces JAR)
- `agents/world-builder.md` — JSON datapack (produces zip)
- `agents/lore-agent.md` — Story content (produces datapack)

For every Forge mod project produced by the Mod Agent, run the asset guard before compiling:
```bash
python3 tools/forge_asset_guard.py --project <mod-project-root> --fix
```

Do not deploy any Forge 1.21.4 mod with missing `assets/<modid>/items/*.json`, blockstates,
models, or PNG textures. Missing client assets cause the purple-and-black Minecraft fallback.

For every generated data pack, run:
```bash
python3 tools/hermes_datapack_guard.py --project <data-pack-root> --fix
```

Do not deploy Minecraft 1.21.4 data packs unless `pack.mcmeta` uses `pack_format: 61` and the guard passes.

Each agent writes its output to `build/`. Pass the output paths to Phase 3.

---

## Phase 3: Deploy

Always run `agents/deploy-agent.md` after any build. Steps:
1. Backup `/mods`
2. Install JAR or datapack
3. Stop server
4. Start server
5. Verify logs show "Done"

---

## Phase 4: Report

Tell Zion what happened in plain, excited language:
- "Done! Your fire dragon is in the game! Look for it in the Nether!"
- "Your rainbow sword is in your creative inventory! It shoots lightning!"
- "The candy dungeon is underground near spawn! Start digging!"

Keep it short, enthusiastic, and specific to what was built. Always include where to find it, how to summon it, or the command to try it right away.

---

## Stop Conditions

**STOP and restore backup if:**
- The Forge build fails 3 times and cannot be fixed
- The server fails to start after 3 restart attempts
- The JAR file does not exist after compilation

**NEVER stop for:**
- Ambiguous requests — interpret creatively
- Missing textures — generate safe placeholder PNGs and run the asset guard
- Complex mob AI — use vanilla mob AI as base
- Low-spec features — simpler is fine, just build it

---

## Completion

- `DEPLOYED` — Mod is installed, server is running, Zion can play
- `DEPLOYED_WITH_WARNINGS` — Deployed but some features were simplified
- `FAILED` — Could not build or deploy. Backup restored. Server running clean.
