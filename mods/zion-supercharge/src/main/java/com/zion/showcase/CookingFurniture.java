package com.zion.showcase;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.FurnaceMenu;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Uses Minecraft's fuel, recipe, XP and inventory save system. */
public final class CookingFurniture extends AbstractFurnaceBlockEntity {
    public CookingFurniture(BlockPos pos, BlockState state) { super(Showcase.COOKING.get(), pos, state, RecipeType.SMELTING); }
    @Override protected Component getDefaultName() { return getBlockState().getBlock().getName(); }
    @Override protected AbstractContainerMenu createMenu(int id, Inventory inventory) { return new FurnaceMenu(id, inventory, this, dataAccess); }
}
