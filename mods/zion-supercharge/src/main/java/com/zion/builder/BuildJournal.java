package com.zion.builder;

import java.util.*;
import net.minecraft.core.*;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.*;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;

/** Persistent per-player, per-dimension construction journal. All mutation runs on the server tick. */
public final class BuildJournal extends SavedData {
    public static final int BLOCKS_PER_TICK=128, MAX_BLOCKS=4096;
    public record Change(BlockPos pos,BlockState before,BlockState after) {}
    public static final class Job {
        public UUID owner; public String name; public List<Change> changes=new ArrayList<>();
        public int placed; public boolean active=true;
    }
    private final Map<UUID,Job> jobs=new LinkedHashMap<>();
    public static BuildJournal get(ServerLevel level) { return level.getDataStorage().computeIfAbsent(new SavedData.Factory<>(BuildJournal::new,BuildJournal::load,null),"zion_builder_journal"); }
    public Job job(UUID owner) { return jobs.get(owner); }
    public void begin(ServerLevel level,UUID owner,RoomPlans.Plan plan) {
        if(jobs.containsKey(owner))throw new IllegalStateException("Keep or undo the previous build before starting another.");
        Job job=new Job(); job.owner=owner;job.name=plan.name();
        for(var entry:plan.blocks().entrySet()) job.changes.add(new Change(entry.getKey(),level.getBlockState(entry.getKey()),entry.getValue()));
        jobs.put(owner,job);setDirty();
    }
    public void advance(ServerLevel level) {
        int budget=BLOCKS_PER_TICK;
        for(Job job:jobs.values()) {
            if(!job.active) continue;
            while(job.placed<job.changes.size()&&budget>0) {
                Change c=job.changes.get(job.placed);
                // Never load distant chunks to continue a build, or overwrite a player edit.
                if(!level.hasChunkAt(c.pos())) break;
                if(!level.getBlockState(c.pos()).equals(c.before()) || level.getBlockEntity(c.pos())!=null) {
                    job.active=false; tell(level,job,"Build paused because the space changed. /zion undo removes the portion already placed.");setDirty();break;
                }
                if(!level.getEntities((net.minecraft.world.entity.Entity)null,new net.minecraft.world.phys.AABB(c.pos())).isEmpty()) {
                    job.active=false;tell(level,job,"Build paused because someone entered its space. /zion undo safely removes the portion already placed.");setDirty();break;
                }
                level.setBlock(c.pos(),c.after(),2);
                job.placed++;budget--;setDirty();
            }
            if(job.placed==job.changes.size()) {job.active=false;tell(level,job,"Your "+job.name.replace('_',' ')+" is ready! /zion find shows where; /zion undo safely removes it.");setDirty();}
            if(budget==0) break;
        }
    }
    public String undo(ServerLevel level,UUID owner) {
        Job job=jobs.get(owner);if(job==null)return "There is no build to undo in this dimension.";
        job.active=false; setDirty(); int restored=0,kept=0;
        // Preflight the complete journal: avoid a half undo caused by unloaded chunks or stored items.
        for(int i=0;i<job.placed;i++) {
            Change c=job.changes.get(i);
            if(!level.hasChunkAt(c.pos()))return "Come near the build before undoing; some of its chunks are unloaded.";
            if(level.getBlockEntity(c.pos()) instanceof Container container&&!container.isEmpty())return "Undo kept the build because furniture contains your items. Empty its storage first.";
        }
        for(int i=job.placed-1;i>=0;i--) {
            Change c=job.changes.get(i);
            if(level.getBlockState(c.pos()).equals(c.after())) {level.setBlock(c.pos(),c.before(),2);restored++;} else kept++;
        }
        jobs.remove(owner);setDirty();
        return "Undid "+restored+" blocks; preserved "+kept+" player changes.";
    }
    public String keep(UUID owner) {
        Job job=jobs.get(owner);
        if(job==null)return "There is no saved build to keep in this dimension.";
        if(job.active)return "Your build is still in progress. Use /zion find to check it before keeping it.";
        if(job.placed!=job.changes.size())return "This build stopped before completion. Use /zion undo before starting another build.";
        jobs.remove(owner);setDirty();
        return "Kept your "+job.name.replace('_',' ')+"! Its blocks and stored items are unchanged. Its undo record is cleared, and you can start another build.";
    }
    private static void tell(ServerLevel level,Job job,String message) {var player=level.getServer().getPlayerList().getPlayer(job.owner);if(player!=null)player.sendSystemMessage(Component.literal(message));}
    public static BuildJournal load(CompoundTag tag,HolderLookup.Provider registries) {
        BuildJournal journal=new BuildJournal();
        ListTag list=tag.getList("Jobs",Tag.TAG_COMPOUND);
        for(int i=0;i<list.size();i++) {
            CompoundTag data=list.getCompound(i);Job job=new Job();job.owner=data.getUUID("Owner");job.name=data.getString("Name");job.placed=data.getInt("Placed");job.active=data.getBoolean("Active");
            ListTag changes=data.getList("Changes",Tag.TAG_COMPOUND);
            for(int j=0;j<changes.size();j++) {var c=changes.getCompound(j);job.changes.add(new Change(BlockPos.of(c.getLong("Pos")),NbtUtils.readBlockState(registries.lookupOrThrow(Registries.BLOCK),c.getCompound("Before")),NbtUtils.readBlockState(registries.lookupOrThrow(Registries.BLOCK),c.getCompound("After"))));}
            job.placed=Math.min(Math.max(job.placed,0),job.changes.size());journal.jobs.put(job.owner,job);
        }
        return journal;
    }
    @Override public CompoundTag save(CompoundTag tag,HolderLookup.Provider registries) {
        ListTag list=new ListTag();
        for(Job job:jobs.values()) {CompoundTag data=new CompoundTag();data.putUUID("Owner",job.owner);data.putString("Name",job.name);data.putInt("Placed",job.placed);data.putBoolean("Active",job.active);ListTag changes=new ListTag();
            for(Change c:job.changes) {CompoundTag ct=new CompoundTag();ct.putLong("Pos",c.pos().asLong());ct.put("Before",NbtUtils.writeBlockState(c.before()));ct.put("After",NbtUtils.writeBlockState(c.after()));changes.add(ct);}data.put("Changes",changes);list.add(data);}
        tag.put("Jobs",list);return tag;
    }
}
