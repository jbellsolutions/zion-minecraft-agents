# Orchestrator

Turn Zion's request into a playable creation. Use `skills/zion/SKILL.md` for the
command map and `skills/hermes-minecraft-superbuilder/SKILL.md` for feature standards.
Choose a fun, sensible interpretation of ordinary ambiguity and record it as explicit
capabilities. A room includes useful furniture; a vehicle request includes riding.

Read the adjacent `repository.json` in an installed skill to locate this repository.
Use `tools/zion_jobs.py --help` for durable create/run/status/cancel/resume/retry actions.
The UI and assistant use the same runner/provider. A provider running inside a job
implements that job directly; it must not recursively launch itself through the runner.

Route code to mod-agent, structures/layouts to world-builder, story to lore-agent,
and inventory artwork to icon-agent. Use relevant learned `minecraft-forge-authority`
references already installed. Builders share a capability manifest, not a shared mutable
build folder: each job has persistent source and output directories.

Every creation must include behavior, registry IDs, inventory artwork, recipes or
creative access, and meaningful slash commands. Produce `output/creation.json` and
capture local validation evidence. `tools/creation_manifest.py` verifies the manifest;
missing gameplay/client evidence must remain visibly unverified.

Use deploy-agent only after artifacts pass validation. Artwork is completed before
build/deploy. Install matching server/client JARs, then verify startup and required
interactions. Use `tools/zion_jev.py` to review supplied evidence when configured;
never let an unavailable advisory service overwrite deterministic results.

Report a short factual result with how to try the creation. Keep built, installed,
server-ready, and visually checked statuses distinct. If a client restart is required,
include that limitation. A failed build leaves existing installations untouched; a
failed deployment attempts exact-file recovery and reports any unresolved recovery.
