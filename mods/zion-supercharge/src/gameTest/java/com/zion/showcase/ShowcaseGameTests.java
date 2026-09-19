package com.zion.showcase;

import com.zion.builder.*;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.*;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.*;

@GameTestHolder("zion_showcase")
public final class ShowcaseGameTests {
    private static final String ARENA="zion_showcase:test_arena";
    @GameTest(template=ARENA,timeoutTicks=20)
    public static void storage_round_trip(GameTestHelper h) {
        for(String kind:List.of("fridge","bookshelf")) {
            BlockPos p=new BlockPos(kind.equals("fridge")?2:4,1,2);h.setBlock(p,Showcase.block(kind));
            StorageFurniture original=h.getBlockEntity(p); Item expected=kind.equals("fridge")?Items.APPLE:Items.BOOK;
            original.setItem(5,new ItemStack(expected,7));
            CompoundTag saved=original.saveWithFullMetadata(h.getLevel().registryAccess());
            StorageFurniture restored=new StorageFurniture(h.absolutePos(p),h.getBlockState(p));restored.loadWithComponents(saved,h.getLevel().registryAccess());
            h.assertTrue(restored.getItem(5).is(expected)&&restored.getItem(5).getCount()==7,kind+" preserves exact inventory count and item on reload");
        }
        h.assertTrue(new ItemStack(Showcase.SWORD.get()).hasFoil(),"Sword has a visible glint");h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=260)
    public static void all_appliances_cook_and_resume(GameTestHelper h) {
        for(int x=2;x<=6;x+=2) {
            String kind=List.of("grill","stove","oven").get((x-2)/2);BlockPos p=new BlockPos(x,1,2);h.setBlock(p,Showcase.block(kind));
            CookingFurniture be=h.getBlockEntity(p);be.setItem(0,new ItemStack(Items.BEEF,2));be.setItem(1,new ItemStack(Items.COAL));
        }
        h.runAtTickTime(60,()->{
            for(int x=2;x<=6;x+=2) {CookingFurniture be=h.getBlockEntity(new BlockPos(x,1,2));CompoundTag save=be.saveWithFullMetadata(h.getLevel().registryAccess());be.loadWithComponents(save,h.getLevel().registryAccess());}
        });
        h.runAtTickTime(220,()->{
            for(int x=2;x<=6;x+=2) {CookingFurniture be=h.getBlockEntity(new BlockPos(x,1,2));h.assertTrue(be.getItem(2).is(Items.COOKED_BEEF)&&be.getItem(2).getCount()==1,"Appliance cooks one beef after fuel/progress reload");h.assertTrue(be.getItem(0).getCount()==1,"Cooking consumes exactly one ingredient");}h.succeed();
        });
    }
    @GameTest(template=ARENA,timeoutTicks=20)
    public static void furniture_sits_and_dismounts(GameTestHelper h) {
        ServerPlayer player=h.makeMockServerPlayerInLevel();BlockPos p=new BlockPos(3,1,3);h.setBlock(p,Showcase.block("chair"));
        player.setPos(h.absolutePos(p).getX()+.5,h.absolutePos(p).getY()+1,h.absolutePos(p).getZ()+.5);h.useBlock(p,player);
        h.assertTrue(player.getVehicle()!=null&&player.getVehicle().getTags().contains("zion_furniture_seat"),"Chair mounts a real seat");
        h.destroyBlock(p);h.assertTrue(player.getVehicle()==null,"Removing furniture safely dismounts its rider");player.discard();h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=30)
    public static void motorcycle_turbo_brake_and_reload(GameTestHelper h) {
        RainbowMotorcycle bike=h.spawn(Showcase.MOTORCYCLE.get(),new BlockPos(30,1,5));ServerPlayer player=h.makeMockServerPlayerInLevel();
        player.startRiding(bike);player.setLastClientInput(new Input(true,false,false,false,true,false,false));
        Vec3 origin=bike.position();double furthest=0;
        // Keep each measured road segment in the arena. Speed is never injected into the vehicle.
        for(int i=0;i<80;i++) {bike.setPos(origin);bike.tick();furthest=Math.max(furthest,bike.position().distanceTo(origin));}
        h.assertTrue(Math.abs(bike.speedMph()-1000)<.1,"Mounted throttle reaches a measured 1,000 mph");
        h.assertTrue(furthest>22.3&&furthest<22.4,"Turbo physically moves22.352blocks per tick");
        player.setLastClientInput(new Input(false,true,false,false,false,false,false));
        for(int i=0;i<20;i++) {bike.setPos(origin);bike.tick();}
        h.assertTrue(bike.speedMph()<.1,"S brake reaches zero");
        CompoundTag saved=bike.saveWithoutId(new CompoundTag());RainbowMotorcycle restored=new RainbowMotorcycle(Showcase.MOTORCYCLE.get(),h.getLevel());restored.load(saved);
        h.assertTrue(restored.speedMph()==0,"Reload starts parked");
        player.stopRiding();h.assertTrue(bike.getPassengers().isEmpty(),"Player can dismount");player.discard();bike.discard();h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=30)
    public static void motorcycle_swept_collision(GameTestHelper h) {
        RainbowMotorcycle bike=h.spawn(Showcase.MOTORCYCLE.get(),new BlockPos(30,1,5));ServerPlayer player=h.makeMockServerPlayerInLevel();player.startRiding(bike);
        player.setLastClientInput(new Input(true,false,false,false,true,false,false));Vec3 origin=bike.position();
        for(int i=0;i<80;i++){bike.setPos(origin);bike.tick();}
        for(int x=27;x<=33;x++) for(int y=1;y<5;y++)h.setBlock(x,y,12,Blocks.STONE);
        bike.setPos(origin);bike.tick();
        h.assertTrue(bike.getZ()+bike.getBbWidth()/2<=h.absolutePos(new BlockPos(0,0,12)).getZ()+1.0e-4,"Turbo cannot tunnel through wall");
        bike.setPos(origin);player.setLastClientInput(Input.EMPTY);bike.tick();h.assertTrue(bike.speedMph()<.1,"Obstacle stops engine momentum");
        player.stopRiding();player.discard();bike.discard();h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=80)
    public static void build_preflight_undo_and_journal_reload(GameTestHelper h) {
        var level=h.getLevel();BlockPos origin=h.absolutePos(new BlockPos(10,1,10));var plan=RoomPlans.create("kitchen",origin);
        h.assertTrue(ZionCommands.preflight(level,plan,origin)==null,"Clear loaded area accepts plan");
        level.setBlock(origin,Blocks.DIAMOND_BLOCK.defaultBlockState(),2);h.assertTrue(ZionCommands.preflight(level,plan,origin)!=null,"Occupied area rejected");level.setBlock(origin,Blocks.AIR.defaultBlockState(),2);
        UUID owner=UUID.randomUUID();BuildJournal journal=BuildJournal.get(level);journal.begin(level,owner,plan);journal.advance(level);
        h.assertTrue(journal.job(owner).placed<=128,"Build stays within per-tick budget");
        BuildJournal restored=BuildJournal.load(journal.save(new CompoundTag(),level.registryAccess()),level.registryAccess());
        h.assertTrue(restored.job(owner).placed==journal.job(owner).placed,"Persistent journal preserves build cursor");
        h.runAtTickTime(20,()->{
            h.assertTrue(!journal.job(owner).active,"Build completes over server ticks");
            BlockPos fridge=origin.offset(1,1,6);StorageFurniture storage=(StorageFurniture)level.getBlockEntity(fridge);storage.setItem(0,new ItemStack(Items.APPLE,2));
            h.assertTrue(journal.undo(level,owner).contains("contains your items"),"Undo refuses to destroy stored items");storage.clearContent();
            BlockPos edit=origin.offset(1,0,1);level.setBlock(edit,Blocks.DIAMOND_BLOCK.defaultBlockState(),2);journal.undo(level,owner);
            h.assertTrue(level.getBlockState(edit).is(Blocks.DIAMOND_BLOCK),"Undo preserves player edits");h.assertTrue(level.getBlockState(fridge).isAir(),"Undo removes unchanged furniture");h.succeed();
        });
    }
    @GameTest(template=ARENA,timeoutTicks=20)
    public static void keep_preserves_build_and_allows_another(GameTestHelper h) {
        var level=h.getLevel();var journal=new BuildJournal();UUID owner=UUID.randomUUID();BlockPos p=h.absolutePos(new BlockPos(5,1,5));
        var plan=new RoomPlans.Plan("kitchen",1,1,1,Map.of(p,Showcase.block("fridge").defaultBlockState()));
        journal.begin(level,owner,plan);
        h.assertTrue(journal.keep(owner).contains("still in progress"),"Cannot discard an active build journal");
        journal.advance(level);StorageFurniture fridge=(StorageFurniture)level.getBlockEntity(p);fridge.setItem(3,new ItemStack(Items.APPLE,9));
        h.assertTrue(journal.keep(owner).contains("Kept your"),"Finished build can be kept");
        h.assertTrue(journal.job(owner)==null,"Keep frees the next build slot");
        h.assertTrue(level.getBlockState(p).is(Showcase.block("fridge"))&&fridge.getItem(3).getCount()==9,"Keep preserves furniture and its inventory");
        var second=new RoomPlans.Plan("bedroom",1,1,1,Map.of(p.offset(2,0,0),Blocks.GOLD_BLOCK.defaultBlockState()));journal.begin(level,owner,second);journal.advance(level);
        h.assertTrue(level.getBlockState(p.offset(2,0,0)).is(Blocks.GOLD_BLOCK),"A second build completes without removing the first");journal.keep(owner);h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=20)
    public static void non_operator_can_place_crafted_motorcycle(GameTestHelper h) {
        var player=h.makeMockPlayer(net.minecraft.world.level.GameType.SURVIVAL);
        h.assertFalse(player.isCreative(),"Placement test uses a survival player");
        h.assertFalse(player.hasPermissions(2),"Test player is not an operator");
        player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,new ItemStack(Showcase.MOTORCYCLE_ITEM.get()));
        BlockPos floor=h.absolutePos(new BlockPos(8,0,8));
        var hit=new net.minecraft.world.phys.BlockHitResult(Vec3.atCenterOf(floor),net.minecraft.core.Direction.UP,floor,false);
        var context=new net.minecraft.world.item.context.UseOnContext(player,net.minecraft.world.InteractionHand.MAIN_HAND,hit);
        var result=Showcase.MOTORCYCLE_ITEM.get().useOn(context);
        h.assertTrue(result.consumesAction(),"Crafted motorcycle can be placed without operator permission");
        h.assertTrue(player.getMainHandItem().isEmpty(),"Successful survival placement consumes exactly its item");
        h.assertEntityPresent(Showcase.MOTORCYCLE.get(),new BlockPos(8,1,8));player.discard();h.succeed();
    }
    @GameTest(template=ARENA,timeoutTicks=260)
    public static void appliance_break_preserves_smelting_experience(GameTestHelper h) {
        BlockPos pos=new BlockPos(4,1,4);h.setBlock(pos,Showcase.block("oven"));CookingFurniture be=h.getBlockEntity(pos);
        be.setItem(0,new ItemStack(Items.ANCIENT_DEBRIS));be.setItem(1,new ItemStack(Items.COAL));
        h.runAtTickTime(220,()->{
            h.assertTrue(be.getItem(2).is(Items.NETHERITE_SCRAP),"Smelting finished before break");
            h.destroyBlock(pos);
            int experience=h.getEntities(net.minecraft.world.entity.EntityType.EXPERIENCE_ORB).stream().mapToInt(net.minecraft.world.entity.ExperienceOrb::getValue).sum();
            h.assertTrue(experience>=2,"Breaking an appliance releases its accumulated smelting experience");h.succeed();
        });
    }
    @GameTest(template=ARENA,timeoutTicks=20)
    public static void queued_build_stops_when_entity_enters(GameTestHelper h) {
        var level=h.getLevel();var journal=new BuildJournal();UUID owner=UUID.randomUUID();BlockPos p=h.absolutePos(new BlockPos(8,1,8));
        var plan=new RoomPlans.Plan("bedroom",1,1,1,Map.of(p,Blocks.STONE.defaultBlockState()));
        journal.begin(level,owner,plan);var pig=h.spawn(net.minecraft.world.entity.EntityType.PIG,new BlockPos(8,1,8));journal.advance(level);
        h.assertTrue(level.getBlockState(p).isAir(),"Queued build does not place a block through an arriving entity");
        h.assertTrue(!journal.job(owner).active&&journal.job(owner).placed==0,"Paused build preserves its cursor");
        h.assertTrue(journal.keep(owner).contains("stopped before completion"),"Partial build cannot silently be accepted as complete");pig.discard();h.succeed();
    }
}
