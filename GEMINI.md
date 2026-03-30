# GEMINI.md — zion-minecraft-agents

Context for Gemini and other AI assistants.

## Project

Kid-friendly Minecraft mod builder for Zion (age 5). He types what he wants,
agents build and install it, the server restarts automatically. Zero steps for Zion.

## Stack

- Minecraft Java Edition 1.21.4
- Forge 54.x mod loader
- Java 21 + Gradle 8.x
- Python 3 (stdlib only) web UI
- Claude Code as the AI runtime

## Key Paths

- Server: `/Users/justin/minecraft-server`
- Mods: `/Users/justin/minecraft-server/mods/`
- Datapacks: `/Users/justin/minecraft-server/world/datapacks/`

## Agents

See `AGENTS.md` for the full pipeline. Short version:
`orchestrator → mod-agent / world-builder / lore-agent → deploy-agent`

## Rules

- Never ask Zion questions — pick the coolest option and run
- Always back up before touching server files
- Always restart the server after installing
- Keep it fun, epic, kid-friendly
