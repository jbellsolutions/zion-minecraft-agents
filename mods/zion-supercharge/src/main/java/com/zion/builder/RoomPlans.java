package com.zion.builder;

import com.zion.showcase.Showcase;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.BlockState;

public final class RoomPlans {
    public static final List<String> NAMES=List.of("bedroom","kitchen","bathroom","sitting_room","chill_room","house");
    public record Plan(String name,int width,int height,int depth,Map<BlockPos,BlockState> blocks) {}
    public static Plan create(String name,BlockPos origin) {
        Map<BlockPos,BlockState> map=new LinkedHashMap<>();
        if(name.equals("house")) {
            shell(map,origin,27,19);
            furniture(map,origin.offset(1,0,1),"kitchen");
            furniture(map,origin.offset(10,0,1),"sitting_room");
            furniture(map,origin.offset(19,0,1),"chill_room");
            furniture(map,origin.offset(1,0,10),"bedroom");
            furniture(map,origin.offset(10,0,10),"bathroom");
            for(int x=1;x<26;x++) if(x!=4&&x!=13&&x!=22) for(int y=1;y<4;y++) put(map,origin,x,y,9,Blocks.SMOOTH_QUARTZ);
            for(int x:new int[]{9,18}) for(int z=1;z<18;z++) if(z!=4&&z!=13) for(int y=1;y<4;y++) put(map,origin,x,y,z,Blocks.SMOOTH_QUARTZ);
            return new Plan(name,27,5,19,map);
        }
        shell(map,origin,9,9); furniture(map,origin,name);
        return new Plan(name,9,5,9,map);
    }
    private static void shell(Map<BlockPos,BlockState> map,BlockPos o,int width,int depth) {
        for(int x=0;x<width;x++) for(int z=0;z<depth;z++) {
            put(map,o,x,0,z,Blocks.OAK_PLANKS); put(map,o,x,4,z,Blocks.SMOOTH_QUARTZ);
            if(x==0||z==0||x==width-1||z==depth-1) for(int y=1;y<4;y++) {
                if(z==0&&x==width/2&&y<=2) continue;
                Block b=(y==2&&x>1&&x<width-2)||(y==2&&z>1&&z<depth-2)?Blocks.LIGHT_BLUE_STAINED_GLASS:Blocks.SMOOTH_QUARTZ;
                put(map,o,x,y,z,b);
            }
        }
        for(int x=2;x<width-1;x+=4) for(int z=2;z<depth-1;z+=4) put(map,o,x,4,z,Blocks.SEA_LANTERN);
    }
    private static void furniture(Map<BlockPos,BlockState> map,BlockPos o,String name) {
        switch(name) {
            case "kitchen" -> {
                place(map,o,1,1,6,"fridge"); place(map,o,2,1,6,"stove"); place(map,o,3,1,6,"oven"); place(map,o,4,1,6,"sink"); place(map,o,6,1,6,"grill");
                place(map,o,2,1,3,"chair"); place(map,o,5,1,3,"chair");
            }
            case "bedroom" -> {
                // Proper two-part bed states; Minecraft can sleep and set a respawn point here.
                map.put(o.offset(2,1,3),Blocks.BLUE_BED.defaultBlockState().setValue(BedBlock.FACING,net.minecraft.core.Direction.SOUTH).setValue(BedBlock.PART,net.minecraft.world.level.block.state.properties.BedPart.FOOT));
                map.put(o.offset(2,1,4),Blocks.BLUE_BED.defaultBlockState().setValue(BedBlock.FACING,net.minecraft.core.Direction.SOUTH).setValue(BedBlock.PART,net.minecraft.world.level.block.state.properties.BedPart.HEAD));
                place(map,o,6,1,6,"bookshelf"); place(map,o,6,1,3,"chair"); put(map,o,1,1,6,Blocks.BARREL);
            }
            case "bathroom" -> { place(map,o,2,1,6,"toilet"); place(map,o,4,1,6,"sink"); place(map,o,6,1,6,"shower"); put(map,o,2,1,3,Blocks.LIGHT_BLUE_CARPET); }
            case "sitting_room" -> { for(int x=2;x<6;x++) place(map,o,x,1,6,"sofa"); place(map,o,1,1,4,"chair"); place(map,o,6,1,4,"bookshelf"); put(map,o,4,1,3,Blocks.WHITE_CARPET); }
            default -> { for(int x=2;x<6;x++) place(map,o,x,1,6,"sofa"); place(map,o,6,1,3,"bookshelf"); put(map,o,2,1,3,Blocks.JUKEBOX); put(map,o,4,1,3,Blocks.PURPLE_CARPET); put(map,o,1,1,6,Blocks.GLOWSTONE); }
        }
    }
    private static void place(Map<BlockPos,BlockState> map,BlockPos o,int x,int y,int z,String name) { put(map,o,x,y,z,Showcase.block(name)); }
    private static void put(Map<BlockPos,BlockState> map,BlockPos o,int x,int y,int z,Block block) { map.put(o.offset(x,y,z),block.defaultBlockState()); }
}
