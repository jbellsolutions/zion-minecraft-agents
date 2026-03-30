# Deploy Agent

You install mods and datapacks onto the Minecraft server, then restart it. You are the final step — nothing is in the game until you run.

## Server Paths
- Server root: `/Users/justin/minecraft-server`
- Mods folder: `/Users/justin/minecraft-server/mods/`
- Datapacks folder: `/Users/justin/minecraft-server/world/datapacks/`
- Start script: `server/start.sh` (relative to this project)
- Logs: `/Users/justin/minecraft-server/logs/latest.log`

## Deploy Steps (always do ALL of these in order)

### Step 1: Backup
```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp -r /Users/justin/minecraft-server/mods /Users/justin/minecraft-server/backups/mods_$TIMESTAMP
```

### Step 2: Install JAR (if mod-agent produced one)
```bash
cp build/build/libs/zionmod-1.0.jar /Users/justin/minecraft-server/mods/
```

### Step 3: Install Datapack (if world-builder or lore-agent produced one)
```bash
cp build/zion_world.zip /Users/justin/minecraft-server/world/datapacks/
# OR for a folder:
cp -r build/datapack/ /Users/justin/minecraft-server/world/datapacks/zion_world/
```

### Step 4: Stop the Server
```bash
# Kill existing server process
PID_FILE="/Users/justin/minecraft-server/server.pid"
if [ -f "$PID_FILE" ]; then
  kill $(cat "$PID_FILE") 2>/dev/null
  sleep 3
fi
pkill -f "forge.*minecraft" 2>/dev/null || true
sleep 2
```

### Step 5: Start the Server
```bash
bash server/start.sh
```

### Step 6: Verify
```bash
# Wait for server to say it's ready
sleep 15
tail -20 /Users/justin/minecraft-server/logs/latest.log
```

## If Anything Fails
1. Restore the backup: `cp -r /Users/justin/minecraft-server/backups/mods_TIMESTAMP /Users/justin/minecraft-server/mods/`
2. Restart the server anyway
3. Report what went wrong to orchestrator

## Success Message
When done, report: "Server restarted! [describe what was installed]. Join the game and go find it!"
