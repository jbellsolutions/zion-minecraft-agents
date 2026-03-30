# Changelog

All notable changes to zion-minecraft-agents are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

## [1.0.0] — 2026-03-29

### Added
- Kid-friendly Minecraft-themed web UI (`ui/index.html` + `ui/server.py`)
- One-click launcher (`🎮 ZION'S MOD BUILDER.command`)
- 5-agent pipeline: orchestrator → mod-agent / world-builder / lore-agent → deploy-agent
- `.claude/settings.json` auto-approves all tools — no permission popups
- AGI-1 framework integration: main-agent orchestrator, healing patterns, learning hooks
- Forge 1.21.4 mod build template in `agents/mod-agent.md`
- JSON datapack support in `agents/world-builder.md`
- Automatic server backup before every deploy
- Server auto-restart after mod installation
- ARCHITECTURE.md, ETHOS.md, AGENTS.md, GEMINI.md, .cursor/rules
- `features.json` task tracker
- `claude-progress.txt` session log
- Healing patterns: Forge build failure, server start failure
- Level 2 persistent agent scaffolding in `.agent/`
- `llms.txt` for LLM consumption
- WALKTHROUGH.md interactive setup guide
- CI/CD via GitHub Actions (`.github/workflows/`)
