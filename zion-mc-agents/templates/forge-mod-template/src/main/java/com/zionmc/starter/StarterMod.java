package com.zionmc.starter;

import com.zionmc.starter.init.ModBlocks;
import com.zionmc.starter.init.ModCreativeTabs;
import com.zionmc.starter.init.ModEntities;
import com.zionmc.starter.init.ModItems;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * StarterMod — main entry point.
 *
 * When the Mod Agent creates a new mod, it copies this template and:
 *   1. Renames the class and package (starter → <modid>)
 *   2. Adds new registry calls in the constructor
 *   3. Implements common setup logic as needed
 */
@Mod(StarterMod.MOD_ID)
public class StarterMod {

    public static final String MOD_ID = "starter";
    public static final Logger LOGGER = LogManager.getLogger(MOD_ID);

    public StarterMod(FMLJavaModLoadingContext context) {
        IEventBus modEventBus = context.getModEventBus();

        // Register all deferred registers with the mod event bus
        ModItems.ITEMS.register(modEventBus);
        ModBlocks.BLOCKS.register(modEventBus);
        ModEntities.ENTITY_TYPES.register(modEventBus);
        ModCreativeTabs.CREATIVE_MODE_TABS.register(modEventBus);

        // Register lifecycle events
        modEventBus.addListener(this::commonSetup);
        modEventBus.addListener(this::clientSetup);

        LOGGER.info("{} mod loading!", MOD_ID);
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
        LOGGER.info("{} common setup complete.", MOD_ID);
    }

    private void clientSetup(final FMLClientSetupEvent event) {
        LOGGER.info("{} client setup complete.", MOD_ID);
    }
}
