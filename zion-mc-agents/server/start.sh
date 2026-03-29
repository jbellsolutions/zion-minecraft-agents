#!/bin/bash
# ============================================================
# Zion's Minecraft Server — Start / Restart Script
# ============================================================
# This script starts (or restarts) the local Forge server.
# It is called by the Deploy Agent after installing mods.
# ============================================================

SERVER_DIR="/Users/justin/minecraft-server"
SERVER_JAR="forge-1.21.4-54.0.0-server.jar"   # Update version as needed
LOG_FILE="$SERVER_DIR/logs/latest.log"
PID_FILE="$SERVER_DIR/server.pid"

# Java settings — tuned for Mac mini M-series
JAVA_OPTS="-Xmx4G -Xms1G -XX:+UseG1GC -XX:+ParallelRefProcEnabled \
  -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions \
  -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
  -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 \
  -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 \
  -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 \
  -XX:InitiatingHeapOccupancyPercent=15 \
  -XX:G1MixedGCLiveThresholdPercent=90 \
  -XX:G1RSetUpdatingPauseTimePercent=5 \
  -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem \
  -XX:MaxTenuringThreshold=1 \
  -Dusing.aikars.flags=https://mcflags.emc.gs \
  -Daikars.new.flags=true"

# ---- Stop any existing server process ----
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Stopping existing server (PID $OLD_PID)..."
    kill "$OLD_PID"
    sleep 10
  fi
  rm -f "$PID_FILE"
fi

# Also check by process name in case PID file is stale
RUNNING_PID=$(pgrep -f "$SERVER_JAR" 2>/dev/null)
if [ -n "$RUNNING_PID" ]; then
  echo "Found running server (PID $RUNNING_PID), stopping..."
  kill "$RUNNING_PID"
  sleep 10
fi

# ---- Start server ----
echo "Starting Minecraft Forge server..."
cd "$SERVER_DIR" || { echo "ERROR: Server directory not found: $SERVER_DIR"; exit 1; }

if [ ! -f "$SERVER_JAR" ]; then
  echo "ERROR: Server JAR not found: $SERVER_DIR/$SERVER_JAR"
  echo "Make sure Forge is installed. See setup guide in the project spec."
  exit 1
fi

# Start server in background, redirect output to log
nohup java $JAVA_OPTS -jar "$SERVER_JAR" nogui >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

echo "Server started with PID $SERVER_PID"
echo "Logs: tail -f $LOG_FILE"
echo ""
echo "Waiting for server to finish loading..."

# Wait up to 120 seconds for server to be ready
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if grep -q "Done (" "$LOG_FILE" 2>/dev/null; then
    echo ""
    echo "✅ Server is ready! Connect at: localhost:25565"
    exit 0
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  printf "."
done

echo ""
echo "⚠️  Server took longer than expected to start."
echo "Check logs: tail -f $LOG_FILE"
exit 1
