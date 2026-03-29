package com.zionmc.starter.init;

import com.zionmc.starter.StarterMod;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * ModEntities — register all custom entity types here.
 *
 * Pattern (replace ExampleEntity with your mob class):
 *
 *   public static final RegistryObject<EntityType<ExampleEntity>> EXAMPLE_MOB =
 *       ENTITY_TYPES.register("example_mob",
 *           () -> EntityType.Builder.<ExampleEntity>of(ExampleEntity::new, MobCategory.MONSTER)
 *               .sized(1.0F, 1.5F)   // width, height
 *               .build("example_mob"));
 *
 * Then in your mod main class or a ClientSetupEvent, register the renderer:
 *   EntityRenderers.register(ModEntities.EXAMPLE_MOB.get(), ExampleRenderer::new);
 */
public class ModEntities {

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, StarterMod.MOD_ID);

    // -------------------------------------------------------------------------
    // Add your entity types below this line:
    // -------------------------------------------------------------------------

}
