# TODOS — zion-minecraft-agents

## Active

- [ ] Set correct Minecraft server path (currently `/Users/justin/minecraft-server` — update if different)
- [ ] Test full mod build pipeline end-to-end (Java 21 + Gradle + Forge)
- [ ] Test deploy + server restart with a simple test mod
- [ ] Verify `🎮 ZION'S MOD BUILDER.command` launches the UI correctly

## Backlog

- [ ] Add voice input to the UI (Web Speech API) so Zion can speak requests
- [ ] Add mod history panel showing past mods Zion created
- [ ] Add "undo last mod" button that restores the backup
- [ ] Add VPS deployment support (server_mode: vps in CLAUDE.md)
- [ ] Add RCON integration to run `/reload` without full server restart
- [ ] Run `/agi-upgrade-l2` to scaffold persistent cross-session agent
- [ ] Run `/agi-sync` after first successful session to seed the genome
- [ ] Add pre-commit hook for secrets scanning

## Completed

- [x] Build kid-friendly web UI
- [x] Create one-click launcher
- [x] Create 5-agent pipeline (orchestrator → specialists → deploy)
- [x] Configure auto-permissions in `.claude/settings.json`
- [x] Apply AGI-1 framework (main-agent, healing, learning)
- [x] Create GitHub repo and push
