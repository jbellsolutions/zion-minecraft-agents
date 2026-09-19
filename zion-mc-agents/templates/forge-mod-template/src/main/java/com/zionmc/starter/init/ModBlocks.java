package com.zionmc.starter.init;

import com.zionmc.starter.StarterMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
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
 *       () -> new Block(blockProperties("my_block")
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
            () -> new Block(blockProperties("example_block")
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
                () -> new BlockItem(block.get(), ModItems.itemProperties(name).useBlockDescriptionPrefix()));
    }

    public static BlockBehaviour.Properties blockProperties(String name) {
        return BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK,
                ResourceLocation.fromNamespaceAndPath(StarterMod.MOD_ID, name)));
    }
}
