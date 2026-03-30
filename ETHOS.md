# ETHOS — zion-minecraft-agents

## Mission

Make Minecraft magical for a 5-year-old. Zion talks, the AI builds, the server restarts. Zero friction between imagination and gameplay.

## Core Principles

**Radical simplicity.** Every decision is made for a child who cannot read terminal output, cannot troubleshoot errors, and cannot wait. If a 5-year-old can't use it with one click, it isn't done.

**Never fail silently.** If something breaks, the server must restore itself from backup and restart. Zion should never log in to find a broken world.

**Always deploy.** A mod that isn't installed isn't real. Every pipeline ends with the server restarted and the new content live.

**Creative over cautious.** When Zion says "add a dragon," we don't ask what color. We pick the coolest version and build it. Ambiguity is resolved in favor of maximum fun.

**Self-healing by default.** Errors are learning opportunities. Every build failure, server crash, or deploy error is logged as a healing pattern so the next run is smarter.

## Quality Bar

- The UI must be usable by a child with no adult supervision
- The deploy pipeline must leave the server in a working state — always
- Every agent must be able to run without asking the user a question
- Every error must be caught, logged, and healed if possible

## What This Repo Will Never Do

- Ask Zion a technical question
- Leave the Minecraft server in a broken state without attempting recovery
- Overwrite mods without a timestamped backup
- Deploy without verifying the JAR compiled successfully
- Expose API keys, credentials, or server paths in logs

## Constraints

- Java Edition 1.21.4 only — no Bedrock, no older versions
- Forge 54.x — no Fabric unless explicitly requested
- Local Mac mini deployment — VPS is opt-in, never default
- Kid-friendly content only — no violence beyond vanilla Minecraft norms
