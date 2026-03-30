#!/bin/bash
# Zion's Minecraft Server Start Script
SERVER_DIR="/Users/justin/minecraft-server"
PID_FILE="$SERVER_DIR/server.pid"
LOG_FILE="$SERVER_DIR/logs/latest.log"

echo "=== Starting Zion's Minecraft Server ==="

# Kill any existing server
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Stopping old server (PID $OLD_PID)..."
    kill "$OLD_PID"
    sleep 4
  fi
fi
pkill -f "forge.*server" 2>/dev/null || true
sleep 2

# Find the Forge server JAR
FORGE_JAR=$(ls "$SERVER_DIR"/*.jar 2>/dev/null | grep -i forge | head -1)
if [ -z "$FORGE_JAR" ]; then
  FORGE_JAR=$(ls "$SERVER_DIR"/forge-*.jar 2>/dev/null | head -1)
fi
if [ -z "$FORGE_JAR" ]; then
  echo "ERROR: Could not find Forge server JAR in $SERVER_DIR"
  exit 1
fi

echo "Using: $FORGE_JAR"

# Start the server
cd "$SERVER_DIR" || exit 1
nohup java \
  -Xmx4G -Xms1G \
  -XX:+UseG1GC \
  -XX:+ParallelRefProcEnabled \
  -XX:MaxGCPauseMillis=200 \
  -XX:+UnlockExperimentalVMOptions \
  -XX:+DisableExplicitGC \
  -XX:+AlwaysPreTouch \
  -XX:G1NewSizePercent=30 \
  -XX:G1MaxNewSizePercent=40 \
  -XX:G1HeapRegionSize=8M \
  -XX:G1ReservePercent=20 \
  -XX:G1HeapWastePercent=5 \
  -XX:G1MixedGCCountTarget=4 \
  -XX:InitiatingHeapOccupancyPercent=15 \
  -XX:G1MixedGCLiveThresholdPercent=90 \
  -XX:G1RSetUpdatingPauseTimePercent=5 \
  -XX:SurvivorRatio=32 \
  -XX:+PerfDisableSharedMem \
  -XX:MaxTenuringThreshold=1 \
  -jar "$FORGE_JAR" nogui \
  > "$LOG_FILE" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"
echo "Server started with PID $SERVER_PID"

# Wait for server to be ready (up to 120 seconds)
echo "Waiting for server to load..."
for i in $(seq 1 60); do
  if grep -q "Done" "$LOG_FILE" 2>/dev/null; then
    echo "=== Server is READY! ==="
    exit 0
  fi
  sleep 2
done

echo "Server is still loading (this is normal for first launch)..."
exit 0
