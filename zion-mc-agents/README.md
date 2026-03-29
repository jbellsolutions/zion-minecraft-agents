# Zion's Minecraft AI Agent Stack

**TenXVA Homeschool Engineering Track — v1.0**

An AI-powered mod development system for Minecraft Java Edition. Zion describes what he wants
in plain English, and a team of specialized Claude Code agents writes the mods, builds the
worlds, generates quest content, and deploys everything automatically into a local server.

---

## How to Use It

Open a terminal in this folder and run:

```bash
claude
```

Then type a prompt like:

```
Make a fire dragon that spawns in the Nether and drops lava crystals when killed.
```

The orchestrator agent will handle everything from there.

---

## Setup Checklist

### 1. Install Prerequisites

```bash
# Java 21 (required for Minecraft 1.21.4)
brew install --cask temurin@21

# Verify Java
java -version   # should show 21

# Node.js 18+
brew install node

# Claude Code
npm install -g @anthropic-ai/claude-code

# Verify Claude Code
claude --version
```

### 2. Set Your API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add this line to your ~/.zshrc or ~/.bash_profile to make it permanent
```

### 3. Install Minecraft Java Edition

Buy and install from [minecraft.net](https://www.minecraft.net). Make sure you can launch the vanilla client.

### 4. Install a Local Forge Server

```bash
# Create server directory
mkdir -p /Users/justin/minecraft-server
cd /Users/justin/minecraft-server

# Download Forge installer for 1.21.4
# Get it from: https://files.minecraftforge.net/net/minecraftforge/forge/
# Then run:
java -jar forge-1.21.4-54.0.0-installer.jar --installServer

# Accept the EULA
echo "eula=true" > eula.txt

# First run (downloads libraries)
java -Xmx4G -jar forge-1.21.4-54.0.0-server.jar nogui
```

### 5. Configure the Server

Edit `/Users/justin/minecraft-server/server.properties`:
```properties
# Whitelist-only (family members only)
white-list=true
enforce-whitelist=true

# Optional: enable RCON for the deploy agent
enable-rcon=true
rcon.password=zionmc123
rcon.port=25575

# Server name
motd=Zion's Minecraft Server
```

Add Zion and Justin to the whitelist:
```bash
# Start the server once, then add players:
# In the server console: whitelist add ZionAlexander
# In the server console: whitelist add Justin
```

### 6. Install Java 21 JDK for Forge Compilation

The Mod Agent needs the JDK to compile mods:
```bash
# Check if already installed
javac -version

# If not, install:
brew install --cask temurin@21
```

### 7. Start the Server

```bash
bash /Users/homebase/Desktop/Zion\ Minecraft\ Agents/zion-mc-agents/server/start.sh
```

### 8. Run Claude Code

From this project directory:
```bash
cd "/Users/homebase/Desktop/Zion Minecraft Agents/zion-mc-agents"
claude
```

Claude Code will automatically read `CLAUDE.md` and know everything about the project.

---

## Project Structure

```
zion-mc-agents/
├── CLAUDE.md                      ← Project context (auto-read by Claude Code)
├── README.md                      ← This file
│
├── agents/
│   ├── orchestrator.md            ← Routes Zion's prompts to specialists
│   ├── mod-agent.md               ← Writes Java mods (Forge/Fabric)
│   ├── world-builder.md           ← Generates biomes and structures
│   ├── lore-agent.md              ← Creates quests and NPC dialogue
│   └── deploy-agent.md            ← Compiles and installs into server
│
├── templates/
│   ├── forge-mod-template/        ← Copy this for each new Forge mod
│   │   ├── build.gradle
│   │   ├── gradle.properties
│   │   ├── settings.gradle
│   │   └── src/main/java/com/zionmc/starter/
│   │       ├── StarterMod.java
│   │       └── init/
│   │           ├── ModItems.java
│   │           ├── ModBlocks.java
│   │           ├── ModEntities.java
│   │           └── ModCreativeTabs.java
│   │
│   └── fabric-mod-template/       ← Copy this for lightweight Fabric mods
│       ├── build.gradle
│       ├── gradle.properties
│       └── src/main/java/com/zionmc/starter/
│           ├── StarterMod.java
│           ├── StarterModClient.java
│           ├── ModItems.java
│           └── ModBlocks.java
│
└── server/
    └── start.sh                   ← Start/restart the Minecraft server
```

---

## Example Prompts to Try

```
Make a fire dragon that spawns in the Nether and drops lava crystals when killed.
```
```
Add a volcano biome with black sand, lava rivers, and obsidian towers.
```
```
Create a quest where I find 3 ancient relics to unlock a secret portal.
```
```
Make a lava crystal sword that sets enemies on fire.
```
```
Build a haunted dungeon structure that spawns in dark oak forests.
```
```
Write me a quest where an old wizard sends me to defeat 5 zombies and brings me back a reward.
```

---

## Homeschool Learning Path

| Phase | Months | What Zion Does |
|-------|--------|----------------|
| 1 — Prompter | 1–2 | Uses plain English to request mods. Learns to give clear, specific instructions. |
| 2 — Reader | 3–4 | Reads the Java code the agent generates. Asks the agent to explain each part. |
| 3 — Collaborator | 5–6 | Writes parts of mods himself, agent fills in the rest. |
| 4 — Developer | 7+ | Writes full mods independently, uses agent for review and new ideas. |

---

## Troubleshooting

### "Claude Code can't find the server"
Check that the server path in `CLAUDE.md` matches your actual server folder.

### "Mod failed to compile"
Ask Claude: `"The mod failed to compile, can you fix the error?"`
Paste in the error output. Claude will fix it automatically.

### "Biome isn't appearing in my world"
Custom biomes only generate in **new chunks**. Explore far from your spawn point,
or delete the world and start fresh.

### "Server won't start"
```bash
# Check for Java version issues
java -version   # must be 21

# Check server logs
tail -50 /Users/justin/minecraft-server/logs/latest.log
```

---

## API Cost Guide

| Request Type | Estimated Cost |
|---|---|
| Simple item mod | ~$0.05–0.15 |
| Custom mob with AI | ~$0.20–0.50 |
| Full quest chain | ~$0.30–0.80 |
| Complete world + mob + quest | ~$0.50–1.50 |

Set a monthly budget cap at [console.anthropic.com](https://console.anthropic.com) to stay safe.

---

*TenXVA — Zion's Minecraft Agent Stack — v1.0*
