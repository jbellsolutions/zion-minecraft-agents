# Zion's Minecraft workshop

Read `AGENTS.md` and `agents/orchestrator.md`. Those are the canonical instructions
for Hermes, the UI runner, Claude, and Codex. Do not use old nested prompts as a
separate pipeline. Use `/zion` or natural language to build, improve, repair, or
manage creations. Command routing is in `skills/zion/SKILL.md`.

Private runtime configuration identifies the existing server, client mod folder,
and exact Java startup arguments. Never infer deployment paths from examples or
change another bot's provider. The target is Forge 54.1.0 on Minecraft 1.21.4.

Inspect the selected job and relevant existing source before updates. Use durable
job state as current evidence; historical progress notes do not establish completion.
