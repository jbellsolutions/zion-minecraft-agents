package com.zionmc.starter;

import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

/**
 * ModItems (Fabric) — register all custom items here.
 *
 * Pattern:
 *   public static final Item MY_ITEM = register("my_item",
 *       new Item(new Item.Settings().maxCount(64)));
 *
 * For items with special right-click or tick behavior, create a subclass.
 */
public class ModItems {

    // -------------------------------------------------------------------------
    // Example item — replace when creating a real mod
    // -------------------------------------------------------------------------
    public static final Item EXAMPLE_ITEM = register("example_item",
            new Item(new Item.Settings().maxCount(64)));

    // -------------------------------------------------------------------------
    // Add your items below this line:
    // -------------------------------------------------------------------------


    // -------------------------------------------------------------------------
    // Registration helper
    // -------------------------------------------------------------------------
    private static Item register(String name, Item item) {
        return Registry.register(Registries.ITEM, StarterMod.id(name), item);
    }

    public static void initialize() {
        // Add items to the vanilla Tools/Combat creative tab for discoverability
        ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS).register(content -> {
            content.add(EXAMPLE_ITEM);
            // Add more items here as you create them
        });
        StarterMod.LOGGER.info("Items registered.");
    }
}
