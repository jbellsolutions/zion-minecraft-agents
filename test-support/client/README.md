# Isolated graphical verification

`java/` is an opt-in development client harness, excluded from the release source set.
It connects only to loopback port25575, an isolated offline test server. Never enable
this source on a production game instance. The server must contain the candidate JAR,
have its own disposable world and grant operator rights to the test player.

Enable the source directory only for a verification build and set JVM properties
`zion.clientProof=true`, `zion.proofDirectory=<absolute directory>` and
`zion.proofArtifact=<candidate JAR SHA256>`. The harness captures the actual game
framebuffer, joins, builds a small test scene, opens inventory, mounts the bike and
tries driving. It records what happened in `client-proof.json`; images need inspection.
It cannot establish success just because the capture sequence finished.

Do not ship this harness in the release JAR. Gameplay GameTests remain separate.
