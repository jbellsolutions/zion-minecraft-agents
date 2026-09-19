package com.zion.showcase;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.*;

@Mod(Showcase.ID)
public final class Showcase {
    public static final String ID = "zion_showcase";
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, ID);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, ID);
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, ID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, ID);
    public static final Map<String, RegistryObject<FurnitureBlock>> FURNITURE = new LinkedHashMap<>();
    public static final RegistryObject<Item> SWORD = ITEMS.register("shiny_sword", () -> new SwordItem(ToolMaterial.NETHERITE, 4, -2.2f, itemProperties("shiny_sword")) {
        @Override public boolean isFoil(ItemStack stack) { return true; }
    });
    public static final RegistryObject<EntityType<RainbowMotorcycle>> MOTORCYCLE = ENTITIES.register("rainbow_motorcycle",
        () -> EntityType.Builder.<RainbowMotorcycle>of(RainbowMotorcycle::new, MobCategory.MISC)
            .sized(2.0f, 1.65f).clientTrackingRange(12).updateInterval(1).setShouldReceiveVelocityUpdates(true)
            .build(ResourceKey.create(Registries.ENTITY_TYPE, id("rainbow_motorcycle"))));
    public static final RegistryObject<Item> MOTORCYCLE_ITEM = ITEMS.register("rainbow_motorcycle", () -> new MotorcycleItem(itemProperties("rainbow_motorcycle").stacksTo(1)));
    static {
        for (String name : new String[]{"fridge", "grill", "stove", "oven", "bookshelf", "chair", "sofa", "sink", "toilet", "shower"}) {
            var block = BLOCKS.register(name, () -> new FurnitureBlock(name,
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id(name)))
                    .mapColor(MapColor.QUARTZ).strength(2.5f).sound(SoundType.METAL).noOcclusion()));
            FURNITURE.put(name, block);
            ITEMS.register(name, () -> new BlockItem(block.get(), itemProperties(name).useBlockDescriptionPrefix()));
        }
    }
    public static final RegistryObject<BlockEntityType<StorageFurniture>> STORAGE = BLOCK_ENTITIES.register("storage",
        () -> new BlockEntityType<>(StorageFurniture::new, java.util.Set.of(block("fridge"), block("bookshelf"))));
    public static final RegistryObject<BlockEntityType<CookingFurniture>> COOKING = BLOCK_ENTITIES.register("cooking",
        () -> new BlockEntityType<>(CookingFurniture::new, java.util.Set.of(block("grill"), block("stove"), block("oven"))));
    public Showcase(FMLJavaModLoadingContext context) {
        IEventBus bus = context.getModEventBus();
        BLOCKS.register(bus); ITEMS.register(bus); ENTITIES.register(bus); BLOCK_ENTITIES.register(bus);
        bus.addListener((net.minecraftforge.event.BuildCreativeModeTabContentsEvent event) -> {
            if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) {
                ITEMS.getEntries().forEach(item -> event.accept(item.get()));
            }
        });
    }
    public static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(ID, path); }
    public static Item.Properties itemProperties(String name) { return new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id(name))); }
    public static Block block(String name) { return FURNITURE.get(name).get(); }
}
