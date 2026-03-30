# AGENTS.md — zion-minecraft-agents

Multi-agent system for Zion's Minecraft mod builder. Each agent has a single job.

## Agent Pipeline

```
User Request
     │
     ▼
orchestrator          ← routes request, never asks questions
     │
     ├──► mod-agent        ← Java mods (mobs, items, blocks, armor, tools)
     ├──► world-builder    ← JSON datapacks (biomes, structures, loot tables)
     ├──► lore-agent       ← Quests, NPC dialogue, books, story
     │
     ▼
deploy-agent          ← installs files, restarts server
```

## Agent Files

| Agent | File | Responsibility |
|-------|------|----------------|
| Orchestrator | `agents/orchestrator.md` | Routes requests, never asks questions |
| Mod Builder | `agents/mod-agent.md` | Java Forge 1.21.4 mods |
| World Builder | `agents/world-builder.md` | JSON datapacks |
| Lore Writer | `agents/lore-agent.md` | Story, quests, books |
| Deployer | `agents/deploy-agent.md` | Install + server restart |
| Session Orchestrator | `.claude/agents/main-agent.md` | Repo health brief + routing |

## AGI-1 Integration

This repo runs on the [AGI-1 framework](https://github.com/jbellsolutions/agi-1).

Install AGI-1 then open this repo in Claude Code:
```bash
git clone https://github.com/jbellsolutions/agi-1 ~/.claude/skills/agi-1
cd ~/.claude/skills/agi-1 && ./setup
```

Available commands once installed:
- `/agi-main` — Session orchestrator with repo health brief
- `/agi-1` — Full upgrade pipeline
- `/agi-heal` — Fix errors against known patterns
- `/agi-learn` — Extract insights from observations
- `/agi-audit` — Score the repo (G-Stack + AI Blueprint)

## Rules

1. Orchestrator NEVER asks clarifying questions — makes a creative decision and runs
2. Deploy agent ALWAYS backs up before changing anything
3. Deploy agent ALWAYS restarts the server after installing
4. If deployment fails, restore the backup and restart the server
5. Keep everything kid-friendly — Zion is 5 years old
