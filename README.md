<div align="center">

# Zy Java Coding Mod Academy

### Type what you want. The AI builds it. Your server restarts. Zero steps.

[![Claude Code](https://img.shields.io/badge/Runs%20on-Claude%20Code-6366f1)](https://claude.ai/code)
[![Minecraft Forge](https://img.shields.io/badge/Minecraft-Forge%201.21.4-00AA00?logo=minecraft)](https://files.minecraftforge.net)
[![Java 21](https://img.shields.io/badge/Java-21-orange?logo=openjdk)](https://openjdk.org/projects/jdk/21/)
[![Part of Zy AI Academy](https://img.shields.io/badge/Part%20of-Zy%20AI%20Academy-blue)](https://zyaiacademy.com)

</div>

---

## Welcome

This is the Java Minecraft Mod Builder from Zy AI Academy — the same AI system Zion uses to build real mods for his own Minecraft server.

Your child types something like:

> "Add a fire dragon that spawns in the Nether"

And the AI:
1. Writes the Java Forge mod
2. Compiles it
3. Installs it on your server
4. Backs up your existing mods first (automatically)
5. Restarts the server
6. Tells you it's done ✅

No coding required from the parent. No command line. Just plain English.

---

## Before We Start — Do You Have Hermes Installed?

This system runs on **Hermes**, a self-improving AI agent that gets smarter every time it builds a mod.

Answer one question and follow the right path:

**Open your Terminal app (Mac: press `⌘ + Space`, type "Terminal", hit Enter) and type:**

```bash
hermes
```

---

### ✅ YES — Hermes is installed (it opened or showed a menu)

You're ready. Jump to Step 2.

---

**Step 2: Clone this repo**

```bash
git clone https://github.com/jbellsolutions/zion-minecraft-agents
```

**Step 3: Run the setup script**

```bash
cd zion-minecraft-agents && ./setup.sh
```

The setup script will:
- Ask where your Minecraft server is located
- Configure all 5 agents with your server path
- Verify Java 21 and Claude Code are installed
- Make everything executable

**Step 4: Open the repo in Claude Code**

```bash
claude zion-minecraft-agents/
```

Then type your first request:

```
/zion make something cool
```

---

### ❌ NO — Hermes isn't installed yet

No problem. It takes about 5 minutes.

**Step 1: Install Hermes**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

```bash
source ~/.zshrc
```

Verify it worked:

```bash
hermes
```

You should see a menu. If you do, Hermes is installed.

**Step 2: Set up Telegram (optional — lets you talk to it from your phone)**

```bash
hermes gateway setup
```

Follow the prompts — it walks you through creating a Telegram bot in 2 minutes. When done:

```bash
hermes gateway start
```

Now you can send your child's mod requests from your phone and get back a "done!" message when the server restarts.

**Step 3: Now follow the YES path above** — clone the repo, run setup.sh, open in Claude Code.

---

## What Gets Installed

| Agent | What It Does |
|-------|-------------|
| **Orchestrator** | Routes your child's requests — never asks questions, just picks the coolest version and builds it |
| **Mod Agent** | Writes Java Forge 1.21.4 mods (mobs, items, blocks, weapons, bosses) — full source, compiles first try |
| **World Builder** | Generates biomes, structures, dungeons, terrain |
| **Lore Agent** | Creates quests, NPC dialogue, data packs, books |
| **Deploy Agent** | Backs up mods, compiles, installs JAR, restarts server — then confirms it's live |
| **Icon Agent** | Generates a Minecraft-style pixel art icon for every mod your child builds |

All agents run with Zion's rules:
- Never leave the server broken
- Always backup before installing
- Keep everything kid-friendly
- Never ask a question — just build the coolest version

---

## How to Use It

Once set up, your child opens Claude Code in the repo folder and just types:

```
Add a fire dragon boss in the Nether
```

```
Make a sword that shoots lightning
```

```
Create a new biome with rainbow trees
```

```
Add a villager that sells enchanted diamond tools
```

Or use the slash command:

```
/zion <whatever your child wants>
```

The agents figure out the rest. One request in → working mod in the game.

---

## Rollback

If a mod breaks something, type:

```
/rollback
```

The deploy agent lists your last 5 backups and restores whichever one you pick. Server comes back up clean.

---

## Mod Library

Every mod your child builds gets added to `mods/library.json` automatically — name, type, date, icon. The UI at `http://localhost:8080` shows your whole collection as a browsable card grid.

---

## Requirements

Before running setup.sh, make sure you have:

| Requirement | How to Install |
|-------------|---------------|
| macOS (tested on Mac mini M-series) | — |
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` |
| Java 21 | `brew install openjdk@21` |
| Minecraft Forge 1.21.4 server (set up locally) | [forge.minecraftforge.net](https://files.minecraftforge.net) |
| Hermes agent | `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh \| bash` |

For icon generation (optional):
- `OPENAI_API_KEY` in your environment (for DALL-E pixel art icons)

---

## Dropped This Into Claude Code or Codex?

If you're reading this inside an AI session and want the AI to walk you through setup interactively, say:

> "Walk me through setting up the Minecraft mod builder. Start by checking if Hermes is installed."

The AI will check your environment, ask the right questions, and configure everything step by step.

---

## Part of Zy AI Academy

This is the free coding bonus included with every Zy AI Academy purchase.

← [Back to Zy AI Academy](https://github.com/jbellsolutions/zy-ai-academy)
🌐 [zyaiacademy.com](https://zyaiacademy.com)
