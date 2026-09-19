# Deployment and recovery

`tools/zion_deploy.py` installs explicit hashed artifacts on the configured host.
It does not contact another host, change the Hermes provider, or choose a server.
Runtime paths and startup arguments are held in an ignored private JSON file.

## Hermes command discovery

Install the repository skills with `tools/install_hermes_skills.py --hermes-home
<selected-home>`. This preserves learned authority skills and refuses duplicate names.
For Hermes versions that alphabetically clip Telegram skills at 100 commands, use
`tools/patch_hermes_menu.py --hermes-root <installed-runtime> --hermes-home <selected-home>`
to preview the narrow compatibility patch, then repeat with `--apply`. The patch keeps
core and plugin precedence and prioritizes the enabled `/zion` skill within the remaining
skill slots. It never creates a disabled or missing command. Restart the selected gateway
to register the menu and verify it through Telegram's read-only command inventory.

The patch backs up runtime source privately and is idempotent. After upgrading Hermes,
check whether the upstream menu implementation now has native pinning support; otherwise
reapply the reviewed patch. The utility refuses unfamiliar collector layouts rather than
guessing. Model/provider settings and credentials are outside its scope.

## Private runtime configuration

```json
{
  "server_root": "/absolute/path/to/minecraft-server",
  "client_mods": "/absolute/path/to/minecraft/mods",
  "level_name": "world",
  "start_argv": ["/absolute/path/to/java", "-Xmx4G", "-jar", "forge-server.jar", "nogui"],
  "startup_timeout_seconds": 180,
  "stop_timeout_seconds": 90
}
```

Use the installed server's verified launch arguments, including Forge's argument
files when appropriate. The process must launch Java directly with its working
directory at `server_root`; do not put shell commands or credentials in the array.
Use canonical paths (on macOS `/private/tmp`, rather than its `/tmp` symlink).
Select the real `level-name` from server.properties, not an assumed default.
Keep this file as `.zion/runtime.private.json` or another private path.

For an already running server, use `adopt --pid <pid>`. Adoption verifies the sole
Java process with that exact working directory and records its start time. Unowned
or ambiguous processes block deployment. Stops use SIGTERM and wait for graceful
exit; there is no force-kill fallback. Readiness requires a fresh launch log and a
live process, so old `Done` lines cannot produce success.

## Validated artifact handoff

The job must first produce a valid `creation.json`. It contains every capability,
asset, command, artifact, and available evidence. Deployment re-runs
`creation_manifest.validate_manifest(require_evidence=False)` against the actual
files and checks that every JAR has a passed compile report tied to its SHA-256.
Runtime/client checks may still be pending before the first installation.

A deployment manifest adds explicit destination filenames and replacement hashes:

```json
{
  "schema_version": 1,
  "job_id": "shiny_sword",
  "minecraft": "1.21.4",
  "forge": "54.1.0",
  "creation_manifest": "creation.json",
  "creation_sha256": "<SHA-256 of creation.json>",
  "artifacts": [
    {
      "kind": "mod",
      "source": "artifacts/shiny_sword-2.jar",
      "filename": "shiny_sword-2.jar",
      "sha256": "<SHA-256 of the built JAR>",
      "replaces": [{"filename": "shiny_sword-1.jar", "sha256": "<SHA-256 of installed version>"}]
    }
  ]
}
```

All paths are relative to the deployment manifest, or explicit canonical absolute
paths. The corresponding creation artifact must reference those same bytes. Use
`kind: datapack` with a `.zip` filename for data packs. Archives must have pack.mcmeta
at the root. Omit `replaces` for a new creation. Collisions with unknown files fail.
JARs go to both server and client; data packs go only to the selected world/datapacks.

```bash
python3 tools/zion_deploy.py --config .zion/runtime.private.json plan --manifest .zion/jobs/JOB/output/deployment.json
python3 tools/zion_deploy.py --config .zion/runtime.private.json deploy --manifest .zion/jobs/JOB/output/deployment.json --stop-client
```

`--stop-client` permits a graceful close of the affected Minecraft client, identified
by its Java process and exact game directory. Without it an open affected client
blocks installation. Client launch arguments, which may contain access tokens, are
never printed or saved. Relaunch and visually verify the client after installation;
server startup does not establish client rendering or gameplay success.

The tool locks deployment, snapshots exact affected files and validated inputs,
stops the server, then snapshots the complete world and Minecraft configuration
before installing. It does not delete session.lock or prune backups. Backups and
journals stay under the private server `.zion-deploy` directory. Disk/backup errors
stop installation. A failed startup restores tracked files and the fresh stopped-world
snapshot before restarting the previous server when it was originally running.

## Rollback

```bash
python3 tools/zion_deploy.py --config .zion/runtime.private.json history
python3 tools/zion_deploy.py --config .zion/runtime.private.json rollback --transaction TRANSACTION --stop-client
```

Normal rollback restores only transaction-owned files, preserves unrelated mods,
and leaves subsequent world progress intact. Changed artifact hashes block rollback
before stopping the server. An interrupted transaction must be recovered before a
new deployment. Keep its journal and backups until recovery is complete.

World restoration after a successful deployment is a separate deliberate operation:
stop the server, inspect `world-status`, and pass the current stopped-world SHA-256
with `rollback --restore-world-fingerprint HASH`. It rejects a changed fingerprint.
This rewinds the selected world to the snapshot and therefore discards later progress;
use only when that restoration is authorized. Ordinary `/zion rollback` preserves
world progress. Neither kind of file rollback is a construction-command undo feature.

The immutable backup is never merged wholesale into mods. Removing custom registries
can still affect world compatibility; verify recovery and report unresolved issues.
