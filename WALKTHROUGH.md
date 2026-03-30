> **To install:** Open Claude Code in this folder and type `set this up for me` or `/walkthrough`

# WALKTHROUGH — zion-minecraft-agents

Step-by-step setup guide for Zion's Minecraft Mod Builder.

---

## What This Is

An AI pipeline that turns Zion's natural language requests into installed Minecraft mods. He types "add a fire dragon," hits the button, and 2-5 minutes later he's fighting a fire dragon in his world.

---

## Prerequisites

- macOS (tested on Mac mini M-series)
- Python 3.x (pre-installed on Mac — verify: `python3 --version`)
- Java 21 (`brew install openjdk@21` or download from adoptium.net)
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Minecraft Forge 1.21.4 server already set up
- AGI-1 framework: `git clone https://github.com/jbellsolutions/agi-1 ~/.claude/skills/agi-1 && cd ~/.claude/skills/agi-1 && ./setup`

---

## Install Steps

### Step 1: Clone the repo
```bash
git clone https://github.com/jbellsolutions/zion-minecraft-agents
```

### Step 2: Set your server path
Edit two files to point to your actual Minecraft server:
- `CLAUDE.md` — update the `Server path` line
- `agents/deploy-agent.md` — update all path references

Default: `/Users/justin/minecraft-server`

### Step 3: Open in Claude Code
```bash
cd zion-minecraft-agents
claude
```

The `.claude/settings.json` auto-approves all tool permissions — no popups.

### Step 4: Test it
Type in Claude Code:
```
/zion add a simple glowing stone block
```

This should: build a Forge mod, install it, restart the server.

---

## Launch Zion's UI

**Option A — Double-click:** `🎮 ZION'S MOD BUILDER.command` on the Desktop.

**Option B — Terminal:**
```bash
python3 ui/server.py
```
Browser opens at `http://localhost:8765`.

---

## Slash Commands (after AGI-1 install)

| Command | What It Does |
|---------|-------------|
| `/zion <request>` | Build and deploy a mod for Zion |
| `/agi-main` | Session health brief + routing |
| `/agi-1` | Full AGI-1 upgrade pipeline |
| `/agi-heal` | Fix a specific error against known patterns |
| `/agi-audit` | Score the repo (G-Stack + AI-Readiness) |
| `/agi-learn` | Extract insights from accumulated observations |

---

## Troubleshooting

**UI doesn't open:** Make sure port 8765 is free: `lsof -ti:8765 | xargs kill -9`

**Server doesn't restart:** Check the server path in `agents/deploy-agent.md` matches your actual Minecraft server location.

**Build fails:** Make sure Java 21 is installed: `java -version`. Gradle 8 requires Java 17+.

**Claude not found:** Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

---

## File Map

```
🎮 ZION'S MOD BUILDER.command  ← Double-click launcher
ui/index.html                   ← Kid-friendly UI
ui/server.py                    ← Local web server
agents/orchestrator.md          ← AI routing logic
agents/mod-agent.md             ← Java mod builder
agents/world-builder.md         ← Datapack builder
agents/lore-agent.md            ← Story/quest writer
agents/deploy-agent.md          ← Install + restart
server/start.sh                 ← Server restart script
.claude/settings.json           ← Auto-permissions + hooks
```
