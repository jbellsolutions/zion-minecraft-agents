package com.zion.showcase;

import net.minecraft.core.*;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public final class StorageFurniture extends RandomizableContainerBlockEntity {
    private NonNullList<ItemStack> inventory = NonNullList.withSize(27, ItemStack.EMPTY);
    public StorageFurniture(BlockPos pos, BlockState state) { super(Showcase.STORAGE.get(), pos, state); }
    @Override public int getContainerSize() { return 27; }
    @Override protected Component getDefaultName() { return getBlockState().getBlock().getName(); }
    @Override protected NonNullList<ItemStack> getItems() { return inventory; }
    @Override protected void setItems(NonNullList<ItemStack> items) { inventory=items; }
    @Override protected AbstractContainerMenu createMenu(int id, Inventory playerInventory) { return ChestMenu.threeRows(id, playerInventory, this); }
    @Override protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        inventory=NonNullList.withSize(getContainerSize(), ItemStack.EMPTY);
        ContainerHelper.loadAllItems(tag, inventory, registries);
    }
    @Override protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        ContainerHelper.saveAllItems(tag, inventory, registries);
    }
}
