---
name: forge-1214-assets
description: Use when creating or fixing Minecraft Java Edition Forge 54.x / Minecraft 1.21.4 mods with custom items, blocks, models, or textures, especially when purple-and-black missing textures appear.
---

# Forge 1.21.4 Asset Guard

Purple-and-black blocks/items mean Minecraft could not resolve the client model or texture. In
Forge 54.x for Minecraft 1.21.4, Java registration is not enough; the mod jar must include the
matching resource-pack files under `src/main/resources/assets/<modid>/`.

## Required workflow

1. Read `gradle.properties` and use the exact `mod_id`.
2. Find every registry name passed to `ITEMS.register`, `BLOCKS.register`, or the local block helper.
3. Create all required asset files before building.
4. Run:
   ```bash
   python3 tools/forge_asset_guard.py --project <mod-project-root> --fix
   ```
5. Build only after the guard reports `Forge asset guard passed.`

## Pack metadata

For Minecraft 1.21.4:
```json
{
  "pack": {
    "pack_format": 46,
    "description": "<mod name> resources"
  }
}
```

## Standalone item contract

For registry name `lava_crystal`:
```
assets/<modid>/items/lava_crystal.json
assets/<modid>/models/item/lava_crystal.json
assets/<modid>/textures/item/lava_crystal.png
```

`items/lava_crystal.json`:
```json
{
  "model": {
    "type": "minecraft:model",
    "model": "<modid>:item/lava_crystal"
  }
}
```

`models/item/lava_crystal.json`:
```json
{
  "parent": "minecraft:item/generated",
  "textures": {
    "layer0": "<modid>:item/lava_crystal"
  }
}
```

## Full block contract

For registry name `crystal_block`:
```
assets/<modid>/blockstates/crystal_block.json
assets/<modid>/models/block/crystal_block.json
assets/<modid>/models/item/crystal_block.json
assets/<modid>/items/crystal_block.json
assets/<modid>/textures/block/crystal_block.png
```

`blockstates/crystal_block.json`:
```json
{
  "variants": {
    "": {
      "model": "<modid>:block/crystal_block"
    }
  }
}
```

`models/block/crystal_block.json`:
```json
{
  "parent": "minecraft:block/cube_all",
  "textures": {
    "all": "<modid>:block/crystal_block"
  }
}
```

`models/item/crystal_block.json`:
```json
{
  "parent": "<modid>:block/crystal_block"
}
```

`items/crystal_block.json`:
```json
{
  "model": {
    "type": "minecraft:model",
    "model": "<modid>:block/crystal_block"
  }
}
```

## Rules

- Asset namespace folder must exactly match `mod_id`.
- Registry names and asset filenames must be lowercase with underscores.
- Texture references omit `.png`; texture files include `.png`.
- PNG textures must be real files, square, and power-of-two sized. Use 16x16 placeholders if custom art is not ready.
- Never leave a registered item or block without its `assets/<modid>/items/<name>.json` file in Minecraft 1.21.4.
