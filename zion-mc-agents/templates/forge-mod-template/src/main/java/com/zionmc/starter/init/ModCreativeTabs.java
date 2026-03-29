package com.zionmc.starter.init;

import com.zionmc.starter.StarterMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

/**
 * ModCreativeTabs — create a custom Creative Mode tab for this mod's items.
 *
 * All items registered in ModItems will appear in this tab.
 * Change the icon() item to be the most iconic item from your mod.
 */
public class ModCreativeTabs {

    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, StarterMod.MOD_ID);

    public static final RegistryObject<CreativeModeTab> STARTER_TAB =
            CREATIVE_MODE_TABS.register("starter_tab",
                    () -> CreativeModeTab.builder()
                            .withTabsBefore(CreativeModeTabs.COMBAT)
                            .icon(() -> ModItems.EXAMPLE_ITEM.get().getDefaultInstance())
                            .displayItems((parameters, output) -> {
                                // Add items to creative tab here:
                                output.accept(ModItems.EXAMPLE_ITEM.get());
                                output.accept(ModBlocks.EXAMPLE_BLOCK.get());
                                // Add more items as they are created...
                            })
                            .title(Component.translatable("itemGroup.starter"))
                            .build());
}
