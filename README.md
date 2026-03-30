# Zion's Minecraft Mod Builder

A plug-and-play AI mod builder for Zion (age 5). He types what he wants, the agents build it, the server restarts. Zero steps.

Built on the [AGI-1 framework](https://github.com/jbellsolutions/agi-1) — self-healing, self-learning.

---

## Install in Claude Code

### Step 1: Install AGI-1
```bash
git clone https://github.com/jbellsolutions/agi-1 ~/.claude/skills/agi-1
cd ~/.claude/skills/agi-1 && ./setup
```

### Step 2: Clone this repo
```bash
git clone https://github.com/jbellsolutions/zion-minecraft-agents
```

### Step 3: Open in Claude Code
Open the `zion-minecraft-agents` folder in Claude Code. The `.claude/settings.json` auto-approves all tools — no permission popups.

### Step 4: Configure server path
Edit `CLAUDE.md` and `agents/deploy-agent.md` to point to your Minecraft server location.

---

## Launch Zion's UI

Double-click `🎮 ZION'S MOD BUILDER.command` on the Desktop.

Or manually:
```bash
python3 ui/server.py
```

Browser opens automatically at `http://localhost:8765`.

---

## How It Works

```
Zion types: "Add a fire dragon boss"
     │
     ▼
orchestrator  →  mod-agent (builds Java Forge mod)
                     │
                     ▼
             deploy-agent (installs JAR, restarts server)
                     │
                     ▼
          ✅ Server restarted. Dragon is in the game!
```

## Agent Pipeline

| Agent | What It Does |
|-------|-------------|
| `orchestrator` | Routes requests, never asks questions |
| `mod-agent` | Builds Java Forge 1.21.4 mods |
| `world-builder` | Builds JSON datapacks |
| `lore-agent` | Writes quests, books, NPC dialogue |
| `deploy-agent` | Installs files, restarts server |

---

## AGI-1 Commands (after installing agi-1)

| Command | What It Does |
|---------|-------------|
| `/agi-main` | Session brief + routing |
| `/agi-1` | Full upgrade pipeline |
| `/agi-heal` | Fix errors against known patterns |
| `/agi-audit` | Score the repo |
| `/agi-learn` | Extract insights from observations |

---

## Requirements

- macOS (tested on Mac mini M-series)
- Python 3 (pre-installed on Mac)
- Claude Code CLI installed
- Java 21 (`brew install openjdk@21`)
- Minecraft Forge 1.21.4 server set up
