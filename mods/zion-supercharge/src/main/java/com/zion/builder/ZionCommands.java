package com.zion.builder;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.zion.showcase.*;
import java.util.*;
import net.minecraft.commands.*;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.registries.ForgeRegistries;
import static net.minecraft.commands.Commands.*;

public final class ZionCommands {
    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        var root=literal("zion").executes(c->help(c.getSource()));
        root.then(literal("help").executes(c->help(c.getSource())));
        root.then(literal("list").executes(c->reply(c.getSource(),"Creations: shiny_sword, rainbow_motorcycle, "+String.join(", ",Showcase.FURNITURE.keySet())+". Rooms: "+String.join(", ",RoomPlans.NAMES))));
        root.then(literal("find").executes(c->{var s=c.getSource();var j=BuildJournal.get(s.getLevel()).job(s.getPlayerOrException().getUUID());return reply(s,j==null?"No saved build here yet. /zion preview house":j.name+" at "+j.changes.get(0).pos().toShortString()+" · "+j.placed+"/"+j.changes.size()+" blocks");}));
        root.then(literal("give").requires(s->s.hasPermission(2)).then(argument("creation",StringArgumentType.word()).suggests((c,b)->SharedSuggestionProvider.suggest(itemNames(),b)).executes(c->{
            String name=StringArgumentType.getString(c,"creation");var item=ForgeRegistries.ITEMS.getValue(Showcase.id(name));
            if(item==null||!itemNames().contains(name))return fail(c.getSource(),"Unknown creation. Use /zion list.");
            var p=c.getSource().getPlayerOrException();if(!p.addItem(new ItemStack(item)))return fail(c.getSource(),"Your inventory is full. Make a free slot first.");return reply(c.getSource(),"Added "+name.replace('_',' ')+" to your inventory.");
        })));
        root.then(literal("spawn").requires(s->s.hasPermission(2)).then(literal("rainbow_motorcycle").executes(c->{
            var p=c.getSource().getPlayerOrException();var v=p.getLookAngle().multiply(3,0,3);var bike=new RainbowMotorcycle(Showcase.MOTORCYCLE.get(),p.level());
            bike.moveTo(p.getX()+v.x,p.getY()+.1,p.getZ()+v.z,p.getYRot(),0);
            if(!p.level().hasChunkAt(bike.blockPosition())||!p.level().noCollision(bike))return fail(c.getSource(),"Find an open spot for your motorcycle.");
            if(!p.level().addFreshEntity(bike))return fail(c.getSource(),"The server did not allow this motorcycle to spawn here.");
            return reply(c.getSource(),"Rainbow motorcycle ready, with Yoda driving! Right-click to join him. W drive, S brake, A/D steer, Space + W turbo, Shift dismount.");
        })));
        root.then(literal("preview").then(argument("room",StringArgumentType.word()).suggests((c,b)->SharedSuggestionProvider.suggest(RoomPlans.NAMES,b)).executes(c->preview(c.getSource(),StringArgumentType.getString(c,"room"),origin(c.getSource())))));
        root.then(literal("place").requires(s->s.hasPermission(2)).then(argument("room",StringArgumentType.word()).suggests((c,b)->SharedSuggestionProvider.suggest(RoomPlans.NAMES,b))
            .executes(c->place(c.getSource(),StringArgumentType.getString(c,"room"),origin(c.getSource())))
            .then(argument("position",BlockPosArgument.blockPos()).executes(c->place(c.getSource(),StringArgumentType.getString(c,"room"),BlockPosArgument.getLoadedBlockPos(c,"position"))))));
        root.then(literal("undo").requires(s->s.hasPermission(2)).executes(c->reply(c.getSource(),BuildJournal.get(c.getSource().getLevel()).undo(c.getSource().getLevel(),c.getSource().getPlayerOrException().getUUID()))));
        root.then(literal("keep").requires(s->s.hasPermission(2)).executes(c->reply(c.getSource(),BuildJournal.get(c.getSource().getLevel()).keep(c.getSource().getPlayerOrException().getUUID()))));
        dispatcher.register(root);
    }
    private static List<String> itemNames() {var names=new ArrayList<String>(Showcase.FURNITURE.keySet());names.add("shiny_sword");names.add("rainbow_motorcycle");return names;}
    private static BlockPos origin(CommandSourceStack source) {return BlockPos.containing(source.getPosition()).offset(4,0,4);}
    public static String preflight(ServerLevel level,RoomPlans.Plan plan,BlockPos origin) {
        if(plan.blocks().size()>BuildJournal.MAX_BLOCKS)return "Build is too large for one safe job.";
        AABB footprint=new AABB(origin.getX(),origin.getY(),origin.getZ(),origin.getX()+plan.width(),origin.getY()+plan.height(),origin.getZ()+plan.depth());
        if(!level.getWorldBorder().isWithinBounds(footprint))return "The build would cross the world border.";
        if(origin.getY()<level.getMinY()||origin.getY()+plan.height()>level.getMaxY()+1)return "The build would cross the world's height limit.";
        for(BlockPos pos:BlockPos.betweenClosed(origin,origin.offset(plan.width()-1,plan.height()-1,plan.depth()-1))) {
            if(!level.hasChunkAt(pos))return "Part of the build is unloaded. Move nearer before placing.";
            if(!level.getBlockState(pos).isAir()||level.getBlockEntity(pos)!=null)return "The space is occupied at "+pos.toShortString()+". Choose a clear area; existing blocks are protected.";
        }
        if(!level.getEntities((Entity)null,footprint).isEmpty())return "An entity is inside the build space. Choose another clear location.";
        return null;
    }
    private static int place(CommandSourceStack source,String name,BlockPos pos)throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        if(!RoomPlans.NAMES.contains(name))return fail(source,"Unknown room. Use /zion list.");
        var journal=BuildJournal.get(source.getLevel());var owner=source.getPlayerOrException().getUUID();
        if(journal.job(owner)!=null)return fail(source,"You already have a saved build. Use /zion keep to keep it and start another, or /zion undo to remove it.");
        var plan=RoomPlans.create(name,pos);String error=preflight(source.getLevel(),plan,pos);if(error!=null)return fail(source,error);
        journal.begin(source.getLevel(),owner,plan);return reply(source,"Building "+name.replace('_',' ')+" at "+pos.toShortString()+". Placing at most 128 blocks each tick; /zion find shows progress.");
    }
    private static int preview(CommandSourceStack source,String name,BlockPos pos) {
        if(!RoomPlans.NAMES.contains(name))return fail(source,"Unknown room. Use /zion list.");var plan=RoomPlans.create(name,pos);
        for(int x=0;x<plan.width();x++) for(int z=0;z<plan.depth();z++) if(x==0||z==0||x==plan.width()-1||z==plan.depth()-1)source.getLevel().sendParticles(ParticleTypes.END_ROD,pos.getX()+x+.5,pos.getY()+.2,pos.getZ()+z+.5,1,0,0,0,0);
        String status=preflight(source.getLevel(),plan,pos);
        return reply(source,name.replace('_',' ')+": "+plan.width()+" × "+plan.depth()+" × "+plan.height()+" blocks, "+plan.blocks().size()+" blocks to place at "+pos.toShortString()+". "+(status==null?"Space is clear. Use /zion place "+name:status));
    }
    private static int help(CommandSourceStack s) {return reply(s,"Zion's creations: /zion list · /zion give shiny_sword · /zion spawn rainbow_motorcycle · /zion preview kitchen · /zion place kitchen [x y z] · /zion find · /zion keep · /zion undo. Keep saves your completed build permanently and lets you start another. Motorcycle: W drive, S brake, A/D steer, Space+W turbo to 1,000 mph on a clear loaded road, Shift dismount. Furniture: right-click to use; cooking needs fuel and ingredients.");}
    private static int reply(CommandSourceStack s,String text) {s.sendSuccess(()->Component.literal(text),false);return 1;}
    private static int fail(CommandSourceStack s,String text) {s.sendFailure(Component.literal(text));return 0;}
}
