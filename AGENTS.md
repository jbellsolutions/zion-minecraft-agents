# Zion Minecraft agents

The root `agents/` directory is canonical. Legacy files under `zion-mc-agents/agents/`
forward here. Use the installed `minecraft-forge-authority` skill's learned patterns;
this repository adds durable jobs, complete assets, and safe deployment.

## Pipeline

1. Orchestrator turns natural language or `/zion` into explicit capabilities.
2. Builder specialists implement source, artwork, commands, and validation evidence.
3. The durable runner validates `output/creation.json`; process exit alone is insufficient.
4. Deployer installs exact validated artifacts to both server and client, then verifies
   server startup. Client rendering and gameplay checks remain separate evidence.

| Agent | Canonical instructions |
| --- | --- |
| Orchestrator | `agents/orchestrator.md` |
| Mod builder | `agents/mod-agent.md` |
| World builder | `agents/world-builder.md` |
| Lore writer | `agents/lore-agent.md` |
| Icon creator | `agents/icon-agent.md` |
| Deployer | `agents/deploy-agent.md` |

## Runtime rules

- Minecraft 1.21.4, Forge 54.1.0, Java 21, Gradle 8.8. Resource-pack format 46;
  data-pack format 61. The Forge template lives in `zion-mc-agents/templates/`.
- Use `tools/zion_jobs.py` and the same Hermes provider for Telegram and UI work.
  Keep workspaces, manifests, cancellation, retries, and evidence durable.
- Preserve existing mod/registry IDs on updates. Give new creations unique namespaces.
- Generate recognizable inventory artwork before compiling; library thumbnails are
  additional previews. Every creation needs useful in-game slash commands.
- Run applicable asset/datapack guards, compile, inspect final artifacts, and validate
  the creation manifest. A guard's metadata repair does not complete missing artwork.
- Use `tools/zion_deploy.py` for all installs and rollbacks. Back up exact affected
  files, gracefully stop the verified server PID, install, start, and check a fresh log.
  Never broadly kill processes, delete session.lock, or replace whole mods/world folders.
- Apply world mutations on the server thread, in bounded batches, with safe placement
  and a separate undo record. Mod-file rollback does not undo world construction.
- Keep credentials, private runtime configuration, chat records, and worlds out of Git.
- Jev checks requirements against evidence via the configured gateway; it is advisory.
  Record unavailable honestly and continue local validation when that service is down.
- Handle ordinary creative ambiguity autonomously. Explain concrete limitations and
  never claim unperformed gameplay or visual checks passed. Keep output friendly for Zion.

Run relevant tests without production side effects. Deployment tests use temporary
server/client folders and fake lifecycle control. Never test failure recovery on Zion's world.
