# Zion's Minecraft Agent Stack

## Purpose
Generate and deploy Minecraft Java mods based on Zion's prompts. This is an AI-powered mod development
system for Minecraft Java Edition 1.21.4 running on a local Mac mini server. Zion describes what he wants
in plain English, and this agent stack writes the mods, builds the worlds, generates quest content, and
deploys everything automatically into the local server.

## Who is Zion?
Zion Alexander is a young homeschool student learning programming through Minecraft modding. He is the
primary user. Keep all responses clear, encouraging, and in plain English. Avoid jargon unless explaining it.
His dad Justin also has server access.

## Server Path
/Users/justin/minecraft-server

## Minecraft Version
1.21.4

## Mod Framework
Forge 54.x (primary) — Fabric 0.15+ available as lightweight alternative

## Java Version
Java 21 (required for 1.21.4)

## Project Structure
```
zion-mc-agents/
  agents/           ← agent system prompts (sub-agents read these)
  templates/        ← starter mod project templates
  server/           ← server start/restart scripts
  CLAUDE.md         ← this file
```

## Agent Roster
| Agent | File | Role |
|---|---|---|
| Orchestrator | agents/orchestrator.md | Routes Zion's prompts to the right specialists |
| Mod Agent | agents/mod-agent.md | Writes Java mods (Forge/Fabric) |
| World Builder | agents/world-builder.md | Generates structures, terrain, biomes |
| Lore Agent | agents/lore-agent.md | Creates quests, NPC dialogue, data packs |
| Deploy Agent | agents/deploy-agent.md | Compiles code and installs into live server |

## Spawning Sub-Agents
When routing to a specialist, use the Task tool to spawn a sub-agent with the appropriate system prompt.
Pass the full context of Zion's request plus any outputs from prior agents in the chain.

Example invocation pattern:
```
Task("mod-agent", system_prompt=<contents of agents/mod-agent.md>, user_message=<Zion's request + context>)
```

## Rules
- Always compile before deploy
- Never overwrite existing mods without creating a timestamped backup first
- Back up /mods to /mods-backup/YYYY-MM-DD-HH-MM before any installation
- Restart server after deploy using server/start.sh
- Report success or errors in plain English to Zion — no stack traces without explanation
- If a compilation error occurs, attempt to fix it before reporting failure
- Keep mod IDs lowercase with underscores (e.g., fire_dragon, lava_crystal)
- Usually pick the coolest safe interpretation and run; ask one short question only when blocked by safety, destructive world changes, incompatible choices, or an unknown target mod
- Run `tools/forge_asset_guard.py --fix` before building/deploying Forge mod source
- Run `tools/hermes_datapack_guard.py --fix` before deploying generated data packs
- All mods go in: /Users/justin/minecraft-server/mods/
- All data packs go in: /Users/justin/minecraft-server/world/datapacks/

## API Budget Awareness
Complex mod generation may use significant tokens. Prefer concise agent messages.
Typical session target: under 50K tokens.

## Whitelist
Server is whitelisted. Only Zion and Justin can connect.
