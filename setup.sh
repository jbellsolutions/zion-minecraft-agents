#!/bin/bash
# zion-minecraft-agents — Setup Script
# Run once after cloning. Works whether or not Hermes is already installed.
set -euo pipefail

echo "==================================="
echo "  Zy Minecraft Mod Builder"
echo "  Setup"
echo "==================================="
echo ""

# ── Python 3 ──────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.11+"
  exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# ── Java 21 ───────────────────────────────────────────────────
if ! command -v java &>/dev/null; then
  echo "⚠️  Java not found. Install it now?"
  read -r -p "   Install via Homebrew? [y/N]: " INSTALL_JAVA
  if [[ "$INSTALL_JAVA" =~ ^[Yy]$ ]]; then
    brew install openjdk@21
    echo 'export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc 2>/dev/null || true
    echo "✅ Java 21 installed"
  else
    echo "   Install manually: brew install openjdk@21"
    echo "   Then re-run this script."
    exit 1
  fi
else
  JAVA_VER=$(java -version 2>&1 | head -1)
  echo "✅ Java: $JAVA_VER"
fi

# ── Claude Code CLI ───────────────────────────────────────────
if ! command -v claude &>/dev/null; then
  echo "⚠️  Claude Code CLI not found. Installing..."
  npm install -g @anthropic-ai/claude-code
  echo "✅ Claude Code installed"
else
  echo "✅ Claude Code: $(claude --version 2>/dev/null || echo 'installed')"
fi

# ── Hermes ────────────────────────────────────────────────────
if command -v hermes &>/dev/null; then
  echo "✅ Hermes: installed"
else
  echo ""
  echo "⚠️  Hermes not found."
  read -r -p "   Install Hermes now? [Y/n]: " INSTALL_HERMES
  if [[ ! "$INSTALL_HERMES" =~ ^[Nn]$ ]]; then
    echo "   Installing Hermes..."
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
    source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true
    echo "✅ Hermes installed"
  else
    echo "   Skipping Hermes. You can install it later:"
    echo "   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
  fi
fi

# ── Server Path ───────────────────────────────────────────────
echo ""
CURRENT_PATH=$(grep -m1 "server path:" CLAUDE.md 2>/dev/null | sed 's/.*server path: //' | tr -d ' ' || echo "/Users/justin/minecraft-server")
echo "Current server path: $CURRENT_PATH"
read -r -p "Where is your Minecraft server? [Press Enter to keep current]: " SERVER_INPUT

if [ -n "$SERVER_INPUT" ]; then
  SERVER_PATH="$SERVER_INPUT"
else
  SERVER_PATH="$CURRENT_PATH"
fi

if [ ! -d "$SERVER_PATH" ]; then
  echo "⚠️  Directory not found: $SERVER_PATH"
  echo "   Create it first, then update CLAUDE.md manually:"
  echo "   server path: /your/server/path"
else
  # Update all agent files with the correct server path
  sed -i '' "s|/Users/justin/minecraft-server|$SERVER_PATH|g" CLAUDE.md
  sed -i '' "s|/Users/justin/minecraft-server|$SERVER_PATH|g" agents/deploy-agent.md
  echo "✅ Server path set to: $SERVER_PATH"
  
  # Create backups directory
  mkdir -p "$SERVER_PATH/backups"
  echo "✅ Backups directory ready: $SERVER_PATH/backups"
fi

# ── Make scripts executable ───────────────────────────────────
chmod +x server/start.sh 2>/dev/null || true
chmod +x "🎮 ZION'S MOD BUILDER.command" 2>/dev/null || true

# ── Create mods library if it doesn't exist ───────────────────
mkdir -p mods/icons
if [ ! -f mods/library.json ]; then
  cat > mods/library.json << 'JSONEOF'
{
  "mods": []
}
JSONEOF
  echo "✅ Mod library created"
fi

# ── Create backups log ────────────────────────────────────────
mkdir -p backups
touch backups/log.txt

echo ""
echo "==================================="
echo "  Setup complete!"
echo ""
echo "  Open Claude Code:"
echo "  claude ."
echo ""
echo "  Then type:"
echo "  /zion make something cool"
echo ""
echo "  Or launch the UI:"
echo "  python3 ui/server.py"
echo "==================================="
