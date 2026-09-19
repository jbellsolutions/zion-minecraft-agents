# Exact artifact deployer

Use `tools/zion_deploy.py` exclusively for game-file deployment. Read
`docs/deployment.md` for the manifest and private runtime configuration. Never infer
paths from old prompts, select arbitrary JARs with wildcards, or replace whole folders.

Before deployment, validate `creation.json` and its compiled artifact hashes. Complete
inventory artwork before the build. Create a deployment manifest from those exact
artifacts; explicit replacement filenames require the existing SHA-256. The tool
revalidates the hashed creation manifest, archive contents, assets, and hash-linked
compile evidence itself. Client rendering/gameplay evidence follows installation.

1. Run `plan` to check all artifacts and destinations without changing the game.
2. Inspect online-player status and coordinate an appropriate restart. Adopt an existing
   server only by its verified exact Java PID and server working directory.
3. Run `deploy`. The tool snapshots affected files, gracefully stops the server, installs
   server/client artifacts, starts the exact Java command, and checks a new startup log.
4. Keep the transaction ID and receipts with the creation. Verify loaded features and
   client behavior; report a required client restart without claiming it already happened.

On failure, the tool attempts exact-file rollback. Never retry by broadly killing Java,
deleting session.lock, or deleting mods/world folders. `history` lists transactions;
`rollback --transaction <id>` restores only files owned by that transaction and rejects
conflicts with later changes. Preserve backups; do not prune them automatically.

Server-file rollback does not undo world construction or remove world data. Loaded
custom registries can remain in saves after removing a mod: validate the recovery result
and report unresolved world compatibility honestly. No failed readiness check is success.
