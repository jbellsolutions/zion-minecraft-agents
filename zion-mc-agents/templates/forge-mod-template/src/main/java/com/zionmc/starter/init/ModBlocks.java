package com.zionmc.starter.init;

import com.zionmc.starter.StarterMod;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.function.Supplier;

/**
 * ModBlocks — register all custom blocks here.
 *
 * Every block also needs a corresponding BlockItem so it appears in the inventory.
 * Use the registerBlockItem helper at the bottom.
 *
 * Pattern:
 *   public static final RegistryObject<Block> MY_BLOCK = registerBlock("my_block",
 *       () -> new Block(BlockBehaviour.Properties.of()
 *           .mapColor(MapColor.STONE)
 *           .requiresCorrectToolForDrops()
 *           .strength(3.0F, 3.0F)
 *           .sound(SoundType.STONE)));
 */
public class ModBlocks {

    public static final DeferredRegister<Block> BLOCKS =
            DeferredRegister.create(ForgeRegistries.BLOCKS, StarterMod.MOD_ID);

    // -------------------------------------------------------------------------
    // Example block — remove or replace when creating a real mod
    // -------------------------------------------------------------------------
    public static final RegistryObject<Block> EXAMPLE_BLOCK = registerBlock("example_block",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.STONE)
                    .requiresCorrectToolForDrops()
                    .strength(3.0F, 3.0F)
                    .sound(SoundType.STONE)));

    // -------------------------------------------------------------------------
    // Add your blocks below this line:
    // -------------------------------------------------------------------------


    // -------------------------------------------------------------------------
    // Helper — registers block + block item together
    // -------------------------------------------------------------------------
    private static <T extends Block> RegistryObject<T> registerBlock(String name, Supplier<T> block) {
        RegistryObject<T> toReturn = BLOCKS.register(name, block);
        registerBlockItem(name, toReturn);
        return toReturn;
    }

    private static <T extends Block> void registerBlockItem(String name, RegistryObject<T> block) {
        ModItems.ITEMS.register(name,
                () -> new BlockItem(block.get(), new Item.Properties()));
    }
}
