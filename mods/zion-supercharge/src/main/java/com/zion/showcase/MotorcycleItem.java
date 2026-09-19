package com.zion.showcase;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;

public final class MotorcycleItem extends Item {
    public MotorcycleItem(Properties properties) { super(properties); }
    @Override public InteractionResult useOn(UseOnContext context) {
        var level = context.getLevel();
        if (level.isClientSide) return InteractionResult.SUCCESS;
        var player = context.getPlayer();
        if (player == null) return InteractionResult.FAIL;
        BlockPos pos = context.getClickedPos().relative(context.getClickedFace());
        var bike = new RainbowMotorcycle(Showcase.MOTORCYCLE.get(), level);
        bike.moveTo(pos.getX() + .5, pos.getY(), pos.getZ() + .5, player.getYRot(), 0);
        if (!level.noCollision(bike) || !level.hasChunkAt(pos)) return InteractionResult.FAIL;
        if (!level.addFreshEntity(bike)) return InteractionResult.FAIL;
        if (!player.isCreative()) context.getItemInHand().shrink(1);
        player.displayClientMessage(Component.literal("Yoda's ready! Right-click to ride. W drives, S brakes, A/D steer, hold Space for 1,000 mph turbo, Shift dismounts."), false);
        return InteractionResult.SUCCESS;
    }
}
