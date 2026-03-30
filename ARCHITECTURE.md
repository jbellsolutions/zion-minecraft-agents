# ARCHITECTURE — zion-minecraft-agents

## Overview

A multi-agent AI pipeline that turns Zion's natural language requests into installed Minecraft mods, with no manual steps.

## Directory Layout

```
zion-minecraft-agents/
├── CLAUDE.md               ← Project context for AI sessions
├── AGENTS.md               ← Agent pipeline documentation
├── ARCHITECTURE.md         ← This file
├── ETHOS.md                ← Project values and constraints
├── WALKTHROUGH.md          ← Interactive setup guide
├── README.md               ← Install instructions
├── features.json           ← Task tracker
├── claude-progress.txt     ← Session log
│
├── agents/                 ← Specialist agent system prompts
│   ├── orchestrator.md     ← Entry point: routes requests
│   ├── mod-agent.md        ← Java Forge mod builder
│   ├── world-builder.md    ← JSON datapack builder
│   ├── lore-agent.md       ← Story/quest/NPC writer
│   └── deploy-agent.md     ← Install + server restart
│
├── ui/                     ← Kid-friendly web interface
│   ├── index.html          ← Minecraft-themed UI (no build step)
│   └── server.py           ← Python stdlib HTTP server (no pip)
│
├── server/
│   └── start.sh            ← Forge server start/restart script
│
├── .claude/                ← Claude Code configuration
│   ├── settings.json       ← Auto-approves all tools + AGI-1 hooks
│   ├── MEMORY.md           ← Repo-local scratchpad (2K cap)
│   ├── GENOME.md           ← Genome privacy notice
│   ├── agents/
│   │   └── main-agent.md   ← Session orchestrator (/agi-main)
│   ├── agi-1/
│   │   └── baseline.json   ← AGI-1 audit scores
│   ├── healing/
│   │   ├── history.json    ← Heal log
│   │   └── patterns/       ← Error → fix patterns (JSON)
│   └── learning/
│       └── observations.json ← Auto-logged failure observations
│
├── .agent/                 ← Level 2 persistent agent
│   ├── agent.py            ← Standalone Python agent
│   ├── identity.json       ← Project identity
│   ├── state.json          ← Cross-session state
│   └── README.md
│
└── genome/
    └── genome.json         ← Local genome snapshot
```

## Data Flow

```
Zion's Request (UI or Claude Code)
         │
         ▼
  orchestrator.md
  ┌──────────────────────────────────────────┐
  │  Reads request, decides which agents     │
  │  are needed. Never asks questions.       │
  └──────┬──────────────┬──────────────┬─────┘
         │              │              │
         ▼              ▼              ▼
   mod-agent      world-builder   lore-agent
   (Java mod)     (datapack)      (story/NPC)
   build/         build/          build/
   build/libs/    datapack/       lore_datapack/
   zionmod-1.0.jar
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
                  deploy-agent
         ┌────────────────────────────────┐
         │  1. Backup /mods               │
         │  2. Install JAR                │
         │  3. Install datapacks          │
         │  4. Stop server                │
         │  5. Start server               │
         │  6. Verify logs                │
         └────────────────────────────────┘
                        │
                        ▼
             ✅ Zion joins and plays
```

## UI Layer

```
Browser (localhost:8765)
    index.html
         │  POST /build {request: "..."}
         ▼
    server.py (Python stdlib HTTPServer)
         │  subprocess.run(["claude", "-p", prompt])
         ▼
    Claude Code CLI
         │  reads CLAUDE.md, runs orchestrator
         ▼
    Agent pipeline (as above)
```

## Key Abstractions

**Agent system prompts** — Markdown files in `agents/` are the full instruction set for each specialist. They are not code; they are instructions Claude reads and follows.

**Deploy-then-restart guarantee** — The deploy-agent always: backs up, installs, stops server, starts server, verifies. This is non-negotiable per ETHOS.

**Auto-healing** — `.claude/settings.json` hooks log every failed bash command to `observations.json` automatically. No manual logging needed.

**Genome** — `~/.claude/agi-1-genome/genome.json` accumulates proven patterns across all repos. Run `/agi-sync` to contribute and inherit.

## Integration Points

| Component | Path | Protocol |
|-----------|------|----------|
| Minecraft server | `/Users/justin/minecraft-server` | Filesystem (JAR copy + shell restart) |
| Forge mod JAR | `build/build/libs/zionmod-1.0.jar` | Compiled by Gradle |
| Datapack | `build/datapack/` | Zip copied to server |
| Server logs | `/Users/justin/minecraft-server/logs/latest.log` | Tail for "Done" |
| Claude CLI | `claude -p "..."` | Subprocess call from server.py |
