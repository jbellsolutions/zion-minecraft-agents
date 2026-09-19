# Zion’s supercharged builder

Approved implementation, September 18, 2026. Preserve Minecraft Java 1.21.4,
Forge 54.1.0, Java 21, existing worlds and legacy registry IDs on Zion’s current Mac.

## Deliverables

1. Configure the existing Hermes Telegram bot with OpenRouter
   `z-ai/glm-5.3-flash`. Back up previous configuration; test real tool calls.
   Keep API keys in private runtime configuration.
2. Use a persistent shared job runner for Telegram and the local builder UI.
   Record requests, attempts, artifacts, cancellation and failures. Stop after
   three failed attempts. Completion requires evidence tied to the built artifact.
3. Require a versioned creation manifest covering requested capabilities, IDs,
   inventory art, world models, commands, artifacts and acceptance evidence.
   Validate Minecraft 1.21.4 item definitions and resource/data formats 46/61.
4. Generate recognizable transparent 64×64 inventory icons. Use dedicated image
   generation, preserve alpha and reject empty or generic square placeholders.
   The shiny sword needs a recognizable blade, metallic highlights and held model.
5. Add Jev evidence review through the existing approved Super Browser gateway.
   Preserve the shared budget and idempotent request IDs. Report supported,
   contradicted, insufficient or unavailable. Deterministic game tests remain required.
6. Add `zion_builder` command ownership and `zion_showcase` content: shiny sword,
   functional furniture and appliances, room presets and a modern house. Placement
   must check loaded space, avoid overwriting occupied blocks and support undo.
7. Build Zion’s requested rainbow motorcycle with Yoda at the handlebars. Make it
   rideable, steerable, persistent and visible with a custom model. Turbo targets
   1,000 mph (447.04 blocks/second assuming one block is one metre), with collision
   and loaded-terrain checks. Display actual speed; stop safely when obstructed.
8. Add discoverable Telegram and Minecraft `/zion` commands for creation, use,
   library, status, cancellation, repairs and rollback. Preserve authorization.
9. Back up and test deployment in isolated server/client copies. Preserve every
   existing mod unless an exact tested compatibility change is documented. Install
   matching artifacts, restart the exact server and roll back failures.
10. Publish source, meaningful tests, installation documentation and an update
    package to a reviewable GitHub branch and pull request.

## Acceptance evidence

Track separately: provider tool calling, Python tests, asset decoding/reference
validation, Java compilation, dedicated-server startup, client join, visual render,
gameplay interactions, restart persistence and client/server artifact parity.
No missing check may be described as passed. Jev reviews the collected evidence;
it cannot substitute for a Minecraft client or gameplay test.
