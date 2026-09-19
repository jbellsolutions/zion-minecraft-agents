package com.zion.showcase.client;

import com.zion.showcase.Showcase;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid=Showcase.ID, bus=Mod.EventBusSubscriber.Bus.MOD, value=Dist.CLIENT)
public final class ShowcaseClient {
    @SubscribeEvent public static void renderers(EntityRenderersEvent.RegisterRenderers event) { event.registerEntityRenderer(Showcase.MOTORCYCLE.get(), MotorcycleRenderer::new); }
}
