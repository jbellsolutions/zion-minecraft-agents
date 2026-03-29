package com.zionmc.starter;

import net.fabricmc.api.ClientModInitializer;

/**
 * StarterModClient (Fabric) — client-only initialization.
 *
 * Use this for:
 * - Registering entity renderers
 * - Registering block entity renderers
 * - Registering screen handlers
 * - Setting up particle effects
 * - Any rendering code that should ONLY run on the client
 */
public class StarterModClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        StarterMod.LOGGER.info("{} client initialized.", StarterMod.MOD_ID);

        // Example: register entity renderer
        // EntityRendererRegistry.register(ModEntities.MY_MOB, MyMobRenderer::new);
    }
}
