#!/bin/bash
# Zion's Minecraft Mod Builder - Double-click to launch!
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python not found" message "Please install Python 3 to run Zion'\''s Mod Builder."'
  exit 1
fi

# Check if Claude Code CLI is available
if ! command -v claude &>/dev/null; then
  osascript -e 'display alert "Claude Code not found" message "Please install Claude Code first. Ask Dad to help!"'
  exit 1
fi

echo "============================="
echo "  Zion's Mod Builder"
echo "  Starting up..."
echo "============================="

python3 ui/server.py
