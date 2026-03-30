# Cursor Rules — zion-minecraft-agents

## Project
Kid-friendly Minecraft mod builder. Zion (age 5) makes requests, agents build and deploy.

## Key Constraints
- Java 21, Forge 1.21.4, Gradle 8.x
- Server at /Users/justin/minecraft-server
- Never ask Zion questions — decide and build
- Always backup before touching server files
- Always restart server after deploy

## Agent Files
- agents/orchestrator.md — entry point
- agents/mod-agent.md — Java mods
- agents/world-builder.md — datapacks
- agents/lore-agent.md — story/quests
- agents/deploy-agent.md — install + restart

## AGI-1 Framework
Self-healing: .claude/healing/patterns/
Self-learning: .claude/learning/observations.json
Session memory: .claude/MEMORY.md
Progress log: claude-progress.txt
