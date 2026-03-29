package com.zionmc.starter.init;

import com.zionmc.starter.StarterMod;
import net.minecraft.world.item.Item;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * ModItems — register all custom items here.
 *
 * Pattern:
 *   public static final RegistryObject<Item> MY_ITEM = ITEMS.register("my_item",
 *       () -> new Item(new Item.Properties().stacksTo(64)));
 *
 * For items with custom behavior, create a class in the item/ package
 * extending Item (or SwordItem, PickaxeItem, etc.) and reference it here.
 */
public class ModItems {

    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, StarterMod.MOD_ID);

    // -------------------------------------------------------------------------
    // Example item — remove or replace when creating a real mod
    // -------------------------------------------------------------------------
    public static final RegistryObject<Item> EXAMPLE_ITEM = ITEMS.register("example_item",
            () -> new Item(new Item.Properties().stacksTo(64)));

    // -------------------------------------------------------------------------
    // Add your items below this line:
    // -------------------------------------------------------------------------

}
