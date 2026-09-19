package com.zion.proof;

import com.google.gson.GsonBuilder;
import java.nio.file.*;
import java.util.*;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.client.tutorial.TutorialSteps;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Development-only harness. Never included in the release source set or JAR. */
@Mod.EventBusSubscriber(modid="zion_showcase", value=Dist.CLIENT)
public final class ClientProof {
    private static boolean connecting;
    private static int ticks, connectedTicks;
    private static final Map<String,Object> report = new LinkedHashMap<>();
    private static Path directory() { return Path.of(System.getProperty("zion.proofDirectory")); }
    private static synchronized void record(String key,Object value) {
        try {
            report.put(key,value);
            Files.createDirectories(directory());
            Files.writeString(directory().resolve("client-proof.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report));
        } catch (Exception error) { throw new IllegalStateException("Cannot record client proof",error); }
    }
    private static void command(Minecraft mc,String command) { mc.getConnection().sendCommand(command); }
    private static void capture(Minecraft mc,String name) {
        Screenshot.grab(directory().toFile(),name+".png",mc.getMainRenderTarget(),message -> record(name,"screenshot callback: "+message.getString()));
    }
    @SubscribeEvent public static void tick(TickEvent.ClientTickEvent.Post event) {
        if (!Boolean.getBoolean("zion.clientProof") || System.getProperty("zion.proofDirectory")==null) return;
        Minecraft mc=Minecraft.getInstance(); ticks++;
        if(ticks==40) {
            record("initial_screen",mc.screen==null?"none":mc.screen.getClass().getName());
            capture(mc,"initial-screen");
            if(mc.screen!=null && mc.screen.getClass().getSimpleName().equals("AccessibilityOnboardingScreen")) mc.setScreen(new TitleScreen());
            if(mc.screen!=null && mc.screen.getClass().getName().equals("net.minecraftforge.client.gui.LoadingErrorScreen")) {
                // Existing legacy packs produce an acknowledged warning. Only activate
                // the explicit proceed control; a fatal loading error has no such button.
                for(var child:mc.screen.children()) if(child instanceof Button button && button.getMessage().getString().equals("Proceed to main menu")) {button.onPress();break;}
            }
        }
        if(ticks>3600) { record("timeout",true);mc.stop();return; }
        if(!connecting && mc.screen instanceof TitleScreen) {
            connecting=true;
            record("artifact_sha256",System.getProperty("zion.proofArtifact","not supplied"));
            record("endpoint","127.0.0.1:25575");
            // Fixed loopback endpoint keeps this harness away from a production server.
            ConnectScreen.startConnecting(new TitleScreen(),mc,ServerAddress.parseString("127.0.0.1:25575"),new ServerData("Zion isolated proof","127.0.0.1:25575",ServerData.Type.OTHER),false,null);
        }
        if(mc.player==null || mc.level==null || mc.getConnection()==null) return;
        connectedTicks++;
        if(connectedTicks==20) {
            record("client_join",true);
            record("player",mc.player.getGameProfile().getName());
            mc.getTutorial().setStep(TutorialSteps.NONE);mc.getToastManager().clear();
            mc.getWindow().setWindowed(1280,720);
            mc.options.fov().set(65);mc.options.renderDistance().set(6);mc.options.guiScale().set(2);
            command(mc,"gamerule sendCommandFeedback false");
            command(mc,"gamemode creative");command(mc,"time set day");command(mc,"weather clear");
            command(mc,"forceload add -64 -64 64 64");command(mc,"tp @s 0 102 0");
        }
        if(connectedTicks==60) {
            command(mc,"fill -12 100 -12 15 100 15 minecraft:smooth_quartz");
            command(mc,"kill @e[type=zion_showcase:rainbow_motorcycle]");
            command(mc,"summon zion_showcase:rainbow_motorcycle 0 101 0 {Rotation:[0f,0f]}");
            String[] blocks={"fridge","stove","oven","grill","bookshelf","chair","sofa","sink","toilet","shower"};
            for(int i=0;i<blocks.length;i++) command(mc,"setblock "+(i%5*2-4)+" 101 "+(i<5?5:8)+" zion_showcase:"+blocks[i]+"[facing=south]");
            command(mc,"clear @s");command(mc,"give @s zion_showcase:shiny_sword");command(mc,"give @s zion_showcase:rainbow_motorcycle");
            for(String block:blocks) command(mc,"give @s zion_showcase:"+block);
            command(mc,"tp @s 8 104 12 145 16");
        }
        if(connectedTicks==160) {mc.options.hideGui=true;mc.getToastManager().clear();}
        if(connectedTicks==180) capture(mc,"showcase-scene");
        if(connectedTicks==190) {command(mc,"tp @s 3.5 101.3 4.5 142 12");mc.options.fov().set(55);}
        if(connectedTicks==210) capture(mc,"motorcycle-hero");
        if(connectedTicks==220) {mc.options.hideGui=false;mc.setScreen(new InventoryScreen(mc.player));}
        if(connectedTicks==250) capture(mc,"inventory-icons");
        if(connectedTicks==280) {mc.setScreen(null);mc.options.setCameraType(CameraType.FIRST_PERSON);command(mc,"tp @s 3 102 5 140 12");}
        if(connectedTicks==320) capture(mc,"held-sword");
        if(connectedTicks==350) {
            command(mc,"tp @s 0 102 0 0 12");
            command(mc,"ride @s mount @e[type=zion_showcase:rainbow_motorcycle,limit=1,sort=nearest]");
            mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
        }
        if(connectedTicks==390) {
            record("mounted_vehicle",mc.player.getVehicle()==null?"none":BuiltInRegistries.ENTITY_TYPE.getKey(mc.player.getVehicle().getType()).toString());
            capture(mc,"yoda-passenger");
        }
        if(connectedTicks==430) {mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);mc.options.keyUp.setDown(true);mc.options.keyJump.setDown(true);}
        if(connectedTicks==450) record("ride_start",List.of(mc.player.getX(),mc.player.getY(),mc.player.getZ()));
        if(connectedTicks==510) {
            record("ride_end",List.of(mc.player.getX(),mc.player.getY(),mc.player.getZ()));
            capture(mc,"turbo-ride");mc.options.keyUp.setDown(false);mc.options.keyJump.setDown(false);
        }
        if(connectedTicks==560) {
            command(mc,"ride @s dismount");record("completed_capture_sequence",true);
        }
        if(connectedTicks==610) mc.stop();
    }
}
