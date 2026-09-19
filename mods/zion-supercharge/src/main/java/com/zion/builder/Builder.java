package com.zion.builder;

import com.zion.showcase.FurnitureBlock;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.common.Mod;

@Mod("zion_builder")
public final class Builder {
    public Builder() {
        MinecraftForge.EVENT_BUS.addListener((RegisterCommandsEvent event) -> ZionCommands.register(event.getDispatcher()));
        MinecraftForge.EVENT_BUS.addListener((TickEvent.ServerTickEvent.Post event) -> {
            for (var level : event.getServer().getAllLevels()) {
                BuildJournal.get(level).advance(level);
                if (level.getGameTime()%40==0) for(var entity:level.getAllEntities()) {
                    if (entity instanceof ArmorStand seat && seat.getTags().contains("zion_furniture_seat")) {
                        var pos=net.minecraft.core.BlockPos.of(seat.getPersistentData().getLong("Furniture"));
                        if (seat.getPassengers().isEmpty() || !(level.getBlockState(pos).getBlock() instanceof FurnitureBlock)) { seat.ejectPassengers(); seat.discard(); }
                    }
                }
            }
        });
    }
}
