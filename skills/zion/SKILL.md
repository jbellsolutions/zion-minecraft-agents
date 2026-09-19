---
name: zion
description: Build, improve, repair, and manage Zion's Minecraft Forge creations, including rooms, functional furniture, houses, vehicles, and distinctive inventory icons. Routes /zion commands and natural language through persistent Hermes jobs.
---

# Zion's Minecraft workshop

Use the repository recorded in the adjacent `repository.json` after installation,
or this skill's repository when working from source. Read `agents/orchestrator.md`
there for the workflow. Keep using the installed `minecraft-forge-authority` skill
and its relevant learned patterns; this skill adds job tracking and quality gates.

## Commands

| Request | Route |
| --- | --- |
| `/zion build <idea>` or `/zion <idea>` | Build a complete playable feature |
| `/zion room <type>` | Furnish a bedroom, kitchen, bathroom, sitting room, or chill room |
| `/zion house <idea>` | Plan connected rooms, doors, lighting, furniture, and a safe placement command |
| `/zion vehicle <idea>` | Create a rideable vehicle with steering, dismounting, collision, and summon access |
| `/zion icon <creation>` | Improve actual inventory textures plus the library preview |
| `/zion repair <creation or symptom>` | Inspect existing source and logs; preserve registry IDs |
| `/zion library` | Show saved creations and their real verification status |
| `/zion status [job]` | Read durable job status; distinguish built, installed, and verified |
| `/zion cancel <job>` | Cancel the selected build via the job runner |
| `/zion rollback <transaction>` | Restore only the exact files recorded by deployment tooling |

Legacy `/icon`, `/library`, `/status`, and `/rollback` requests route here too.
These are assistant commands. Every creation also needs documented in-game slash
commands; do not imply that a Telegram command executes a Minecraft command.

## Execution

1. Turn the request into explicit capabilities and a unique stable creation ID.
   Ordinary ambiguity should produce a creative, sensible default. Preserve existing
   IDs during repairs. Do not silently reduce a motorcycle to a decorative block.
2. Use `tools/zion_jobs.py` for durable create/run/status/cancel/resume/retry operations.
   Read its `--help` for arguments. `tools/zion_provider.py` uses the selected Hermes
   runtime and must produce `output/creation.json`. A successful process exit is not
   proof that the creation works. Do not recursively enqueue jobs from inside a provider job.
3. Use Java 21, Forge 54.1.0, Minecraft 1.21.4, and the Gradle 8.8 wrapper. Work in
   the job's persistent workspace; keep the only source copy out of `/tmp`.
4. Complete behavior, assets, and commands before building. Use `tools/zion_art.py`
   for configured artwork generation, then run applicable source guards and the
   creation-manifest validator. Metadata repair does not finish missing artwork.
5. Follow `agents/deploy-agent.md` for exact artifact deployment. `tools/zion_jev.py`
   provides optional Jev review of requirements against supplied evidence through
   the configured gateway. If unavailable, record that honestly and continue
   deterministic checks; never invent a pass.
6. Report what is ready, how to try it, and any remaining client restart or visual
   verification. Say "built" when built and "installed" only after deployment evidence.

Avoid destructive placement; inspect the site and use empty space when possible.
All block/entity mutations run on the Minecraft server thread, with large structures
placed in bounded batches. Keep the content friendly for Zion.
