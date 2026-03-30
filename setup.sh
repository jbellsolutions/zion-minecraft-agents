#!/bin/bash
# zion-minecraft-agents — Setup Script
# Run once after cloning to configure the environment.
set -euo pipefail

echo "==================================="
echo "  Zion's Minecraft Mod Builder"
echo "  Setup"
echo "==================================="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.11+"
  exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Check Java 21
if ! command -v java &>/dev/null; then
  echo "⚠️  Java not found. Install Java 21 for mod compilation:"
  echo "   brew install openjdk@21"
else
  JAVA_VER=$(java -version 2>&1 | head -1)
  echo "✅ Java: $JAVA_VER"
fi

# Check Claude Code CLI
if ! command -v claude &>/dev/null; then
  echo "❌ Claude Code CLI not found."
  echo "   Install: npm install -g @anthropic-ai/claude-code"
  exit 1
fi
echo "✅ Claude Code: $(claude --version 2>/dev/null || echo 'installed')"

# Check AGI-1
if [ -d ~/.claude/skills/agi-1 ]; then
  echo "✅ AGI-1 framework: installed"
else
  echo "⚠️  AGI-1 not installed. Installing now..."
  git clone https://github.com/jbellsolutions/agi-1 ~/.claude/skills/agi-1
  bash ~/.claude/skills/agi-1/setup --clean
fi

# Make scripts executable
chmod +x server/start.sh
chmod +x "🎮 ZION'S MOD BUILDER.command" 2>/dev/null || true

echo ""
echo "==================================="
echo "  Setup complete!"
echo ""
echo "  To launch Zion's UI:"
echo "  python3 ui/server.py"
echo ""
echo "  Or double-click:"
echo "  🎮 ZION'S MOD BUILDER.command"
echo "==================================="
