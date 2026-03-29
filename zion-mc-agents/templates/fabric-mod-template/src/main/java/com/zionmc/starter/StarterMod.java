package com.zionmc.starter;

import net.fabricmc.api.ModInitializer;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * StarterMod (Fabric) — main initializer.
 *
 * This runs on both client and server at startup.
 * Register items, blocks, entities, and events here.
 *
 * The Mod Agent copies this template and:
 *   1. Renames the class/package (starter → <modid>)
 *   2. Calls ModItems.initialize(), ModBlocks.initialize(), etc.
 *   3. Registers event listeners
 */
public class StarterMod implements ModInitializer {

    public static final String MOD_ID = "starter";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {
        LOGGER.info("Initializing {}!", MOD_ID);

        // Register items, blocks, and entities
        ModItems.initialize();
        ModBlocks.initialize();

        LOGGER.info("{} initialized!", MOD_ID);
    }

    /**
     * Helper to create a mod-namespaced Identifier.
     * Usage: StarterMod.id("my_item")  →  "starter:my_item"
     */
    public static Identifier id(String path) {
        return Identifier.of(MOD_ID, path);
    }
}
