package com.zionmc.starter;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.MapColor;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.sound.BlockSoundGroup;

/**
 * ModBlocks (Fabric) — register all custom blocks here.
 *
 * Pattern:
 *   public static final Block MY_BLOCK = register("my_block",
 *       new Block(AbstractBlock.Settings.create()
 *           .mapColor(MapColor.STONE)
 *           .strength(3.0F, 3.0F)
 *           .sounds(BlockSoundGroup.STONE)
 *           .requiresTool()));
 *
 * Every block also gets a BlockItem so it appears in inventory.
 */
public class ModBlocks {

    // -------------------------------------------------------------------------
    // Example block — replace when creating a real mod
    // -------------------------------------------------------------------------
    public static final Block EXAMPLE_BLOCK = register("example_block",
            new Block(AbstractBlock.Settings.create()
                    .mapColor(MapColor.STONE)
                    .strength(3.0F, 3.0F)
                    .sounds(BlockSoundGroup.STONE)
                    .requiresTool()));

    // -------------------------------------------------------------------------
    // Add your blocks below this line:
    // -------------------------------------------------------------------------


    // -------------------------------------------------------------------------
    // Registration helpers
    // -------------------------------------------------------------------------
    private static Block register(String name, Block block) {
        // Register the block
        Block registeredBlock = Registry.register(Registries.BLOCK, StarterMod.id(name), block);
        // Register the block item so it appears in inventory
        Registry.register(Registries.ITEM, StarterMod.id(name),
                new BlockItem(registeredBlock, new Item.Settings()));
        return registeredBlock;
    }

    public static void initialize() {
        StarterMod.LOGGER.info("Blocks registered.");
    }
}
