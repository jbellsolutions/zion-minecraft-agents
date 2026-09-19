# Zion Supercharged Showcase

This project adds `zion_builder` and `zion_showcase` in one JAR alongside the existing mods. It targets Minecraft Java **1.21.4**, Forge **54.1.0**, and Java **21**. It does not replace legacy registry IDs or edit existing worlds at startup.

Use `/zion spawn rainbow_motorcycle`, then right-click to ride behind the sculpted Yoda driver. **W** accelerates, **S** brakes, **A/D** steers, **Space + W** engages turbo, and **Shift** dismounts. Cruise is 35 mph. Turbo genuinely targets 1,000 mph (447.04 metres/second, treating one block as one metre). The server checks the swept path in 0.25-block steps, at most 90 checks per tick. Obstacles, unloaded road, and world borders stop the bike. A road long and clear enough to sustain that speed is required. Reloaded and unattended motorcycles park automatically.

`/zion give shiny_sword` gives the shiny sword with a dedicated icon and glint. `/zion list` lists all furniture. Fridges and bookshelves have 27 persistent storage slots. Grills, stoves, and ovens use Minecraft's real furnace cooking, fuel, and experience system. Right-click a chair, sofa, or toilet to sit. Sinks and showers play contained water effects without flooding the room.

`/zion preview kitchen` marks the default footprint; `/zion place kitchen` builds there. `bedroom`, `bathroom`, `sitting_room`, `chill_room`, and `house` are also available. An explicit position is accepted by `/zion place house x y z`. Placement refuses occupied space, entities, unloaded chunks, and world-border violations. Jobs persist through world saves and place at most 128 blocks per server tick. `/zion find` reports position and progress. `/zion undo` preserves later player edits and refuses to remove containers holding items. `/zion keep` keeps the completed build and its stored items, clears its undo record, and lets you start another. Keeping an active build is refused.

Creation, spawning, placement, keep, and undo require operator permission. Discovery and help are available to everyone. Ordinary furniture interactions and riding do not require operator permission.

## Build and verify

```sh
python3 ../../tools/forge_asset_guard.py --project . --mod-id zion_showcase --fix
./gradlew clean build
./gradlew -PzionGameTests clean runGameTestServer
```

Tests run in the project's isolated `run` directory. The ten real-game checks cover exact storage save/reload, all three cooking appliances resuming after an inventory/progress round-trip, chair mounting and destruction dismount, actual turbo displacement and braking, high-speed wall collision, persistent build/undo behavior, keeping a completed build, non-operator placement of a crafted motorcycle, smelting experience released when an appliance breaks, and entities entering the build footprint after its initial preflight. They are included only with `-PzionGameTests`. Inspect the test report and log; a Gradle success alone is insufficient because the game launcher can return zero after startup failure.

Client proof uses the separately maintained `test-support/client` source only when `-PzionClientProof` is supplied. Neither proof harness is part of a normal release build. Run a **clean normal build** after development tests to exclude test classes. Forge 54.1.0 runs official Minecraft names, so this project deliberately disables legacy reobfuscation and follows its official MDK's combined classes/resources directory layout.

`generate_resources.py` creates deterministic model, recipe, localization, item-definition, loot, and tag JSON. It never creates placeholder artwork. The sword and motorcycle inventory PNGs are separately generated artwork; furniture inventory appearances use the same custom geometry as the placed blocks.
