package com.zion.showcase.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.zion.showcase.RainbowMotorcycle;
import java.util.*;
import net.minecraft.client.model.geom.*;
import net.minecraft.client.model.geom.builders.*;
import net.minecraft.client.renderer.*;
import net.minecraft.client.renderer.entity.*;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

/** Explicit motorcycle and Yoda geometry, rendered from Minecraft's textured model parts. */
public final class MotorcycleRenderer extends EntityRenderer<RainbowMotorcycle, MotorcycleRenderer.State> {
    private static final ResourceLocation TEXTURE = ResourceLocation.withDefaultNamespace("textures/block/white_concrete.png");
    private final ModelPart model;
    private final Map<String,Integer> colors = new LinkedHashMap<>();
    public static final class State extends EntityRenderState { public float yaw; public float wheelAngle; }
    public MotorcycleRenderer(EntityRendererProvider.Context context) {
        super(context); shadowRadius=.9f;
        MeshDefinition mesh=new MeshDefinition(); PartDefinition root=mesh.getRoot();
        // Local +Z is the motorcycle's front. Model units are 1/16 of a block.
        part(root,"frame",0xffd5e6ef, -1,6,-11,2,2,24);
        part(root,"engine",0xff4d6475,-4,4,-3,8,6,9);
        part(root,"engine_fins",0xffafbac6,-4.4f,5,-3.3f,8.8f,1,9.6f);
        part(root,"seat",0xff161c32,-4,11,-13,8,2,17);
        part(root,"tail_light",0xffff365e,-2.5f,9,-15,5,2,1);
        part(root,"headlight",0xfffff4bc,-2.5f,13,13,5,3,2);
        part(root,"headlight_glass",0xffc5f7ff,-1.5f,13.5f,15,3,2,.5f);
        part(root,"front_fork_left",0xffd8e0f0,-3,4,10,1,11,2);
        part(root,"front_fork_right",0xffd8e0f0,2,4,10,1,11,2);
        part(root,"handlebar",0xffa8bdcf,-8,16,8,16,1,1);
        part(root,"grip_left",0xff111c29,-9,15.5f,7.5f,3,2,2);
        part(root,"grip_right",0xff111c29,6,15.5f,7.5f,3,2,2);
        part(root,"exhaust",0xffa1b4c7,4,4,-13,2,2,13);
        part(root,"exhaust_tip",0xffe7edf5,4,3.5f,-15,2.5f,3,3);
        int[] rainbow={0xffff3154,0xffff922f,0xffffe846,0xff41e89c,0xff3bcbff,0xff7275ff,0xffdc54f4};
        for(int i=0;i<7;i++) {
            part(root,"rainbow_tank_"+i,rainbow[i],-4,8+i*.32f,2+i*.85f,8,3.2f,.88f);
            part(root,"rainbow_tail_"+i,rainbow[i],-4.5f+i*1.28f,9,-14,1.3f,2,4);
            part(root,"rainbow_fender_"+i,rainbow[i],-2.8f+i*.8f,9.4f,8, .82f,1,8);
        }
        for(String end:new String[]{"front","back"}) {
            PartDefinition wheel=root.addOrReplaceChild(end+"_wheel",CubeListBuilder.create(),PartPose.offset(0,4,end.equals("front")?12:-11));
            for(int n=0;n<4;n++) {
                String name=end+"_rubber_"+n;
                wheel.addOrReplaceChild(name,CubeListBuilder.create().texOffs(0,0).addBox(-2,-4,-1.7f,4,8,3.4f),PartPose.rotation(n*(float)Math.PI/4,0,0)); colors.put(name,0xff162031);
            }
            part(wheel,end+"_axle",0xffe5efff,-2.3f,-1,-1,4.6f,2,2);
            for(int n=0;n<4;n++) {
                String name=end+"_spoke_"+n;
                wheel.addOrReplaceChild(name,CubeListBuilder.create().texOffs(0,0).addBox(-2.1f,-2.8f,-.4f,4.2f,5.6f,.8f),PartPose.rotation(n*(float)Math.PI/4,0,0)); colors.put(name,0xff849cbb);
            }
        }
        // Yoda is a visible sculpted driver, with broad pointed ears, eyes and a belted robe.
        part(root,"yoda_robe",0xffc9b88a,-3,13,-1,6,7,5);
        part(root,"yoda_robe_fold",0xffeee1bb,-.7f,13,-1.2f,1.4f,7,5.4f);
        part(root,"yoda_belt",0xff725242,-3.1f,14.5f,-1.1f,6.2f,1,5.2f);
        part(root,"yoda_head",0xff8cbc65,-3.5f,20,-1.2f,7,5.5f,6);
        part(root,"yoda_brow_left",0xff719e51,-3,23,4.5f,2.5f,.8f,.7f);
        part(root,"yoda_brow_right",0xff719e51,.5f,23,4.5f,2.5f,.8f,.7f);
        part(root,"yoda_eye_left",0xff121d12,-2.3f,22,4.85f,1,.9f,.3f);
        part(root,"yoda_eye_right",0xff121d12,1.3f,22,4.85f,1,.9f,.3f);
        part(root,"yoda_nose",0xff9cc871,-.65f,21.6f,4.8f,1.3f,1.3f,1);
        part(root,"yoda_smile",0xff426340,-1,20.9f,4.85f,2,.3f,.3f);
        part(root,"yoda_ear_left",0xff8cbc65,-8,22,0,4.5f,2,1.8f);
        part(root,"yoda_ear_left_tip",0xff8cbc65,-10,22.7f,.2f,2.5f,1,1.2f);
        part(root,"yoda_ear_right",0xff8cbc65,3.5f,22,0,4.5f,2,1.8f);
        part(root,"yoda_ear_right_tip",0xff8cbc65,7.5f,22.7f,.2f,2.5f,1,1.2f);
        part(root,"yoda_ear_inner_left",0xffb4b486,-7.5f,22.4f,1.7f,3.5f,1,.2f);
        part(root,"yoda_ear_inner_right",0xffb4b486,4,22.4f,1.7f,3.5f,1,.2f);
        part(root,"yoda_sleeve_left",0xffc9b88a,-5.2f,15.5f,1.5f,2.5f,3,5);
        part(root,"yoda_sleeve_right",0xffc9b88a,2.7f,15.5f,1.5f,2.5f,3,5);
        part(root,"yoda_hand_left",0xff8cbc65,-5.2f,15.5f,6.5f,2.5f,2,2);
        part(root,"yoda_hand_right",0xff8cbc65,2.7f,15.5f,6.5f,2.5f,2,2);
        part(root,"yoda_boot_left",0xff867654,-4.5f,10,1,3,3,5);
        part(root,"yoda_boot_right",0xff867654,1.5f,10,1,3,3,5);
        model=LayerDefinition.create(mesh,16,16).bakeRoot();
    }
    private void part(PartDefinition parent,String name,int color,float x,float y,float z,float w,float h,float d) {
        parent.addOrReplaceChild(name,CubeListBuilder.create().texOffs(0,0).addBox(x,y,z,w,h,d),PartPose.ZERO); colors.put(name,color);
    }
    @Override public State createRenderState() { return new State(); }
    @Override public void extractRenderState(RainbowMotorcycle bike,State state,float partial) {
        super.extractRenderState(bike,state,partial); state.yaw=bike.getYRot(partial); state.wheelAngle=(bike.tickCount+partial)*bike.speedMph()*.018f;
    }
    @Override public void render(State state,PoseStack pose,MultiBufferSource buffers,int light) {
        pose.pushPose(); pose.mulPose(Axis.YP.rotationDegrees(-state.yaw));
        var vertex=buffers.getBuffer(RenderType.entityCutoutNoCull(TEXTURE));
        model.getChild("front_wheel").xRot=state.wheelAngle; model.getChild("back_wheel").xRot=state.wheelAngle;
        for(var entry:colors.entrySet()) {
            String name=entry.getKey(); boolean front=name.startsWith("front_rubber")||name.startsWith("front_axle")||name.startsWith("front_spoke");
            boolean back=name.startsWith("back_rubber")||name.startsWith("back_axle")||name.startsWith("back_spoke");
            pose.pushPose();
            ModelPart part;
            if(front||back) { ModelPart wheel=model.getChild(front?"front_wheel":"back_wheel"); wheel.translateAndRotate(pose); part=wheel.getChild(name); }
            else part=model.getChild(name);
            part.render(pose,vertex,light,OverlayTexture.NO_OVERLAY,entry.getValue()); pose.popPose();
        }
        pose.popPose(); super.render(state,pose,buffers,light);
    }
}
