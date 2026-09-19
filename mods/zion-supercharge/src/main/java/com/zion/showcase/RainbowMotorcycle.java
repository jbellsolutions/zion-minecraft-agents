package com.zion.showcase;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** Server-authoritative vehicle: client input never supplies a position or speed. */
public final class RainbowMotorcycle extends Entity {
    public static final double TURBO_BLOCKS_PER_TICK = 1000.0 * 0.44704 / 20.0;
    public static final double CRUISE_BLOCKS_PER_TICK = 35.0 * 0.44704 / 20.0;
    private static final double SUBSTEP = 0.25;
    private static final EntityDataAccessor<Float> SPEED = SynchedEntityData.defineId(RainbowMotorcycle.class, EntityDataSerializers.FLOAT);
    private double speed;
    private double verticalSpeed;
    private int lerpSteps;
    private double lerpX, lerpY, lerpZ;
    private float lerpYaw;
    private boolean safetyBrake;

    public RainbowMotorcycle(EntityType<? extends RainbowMotorcycle> type, Level level) {
        super(type, level);
        blocksBuilding = true;
    }
    @Override protected void defineSynchedData(SynchedEntityData.Builder builder) { builder.define(SPEED, 0f); }
    @Override protected void readAdditionalSaveData(CompoundTag tag) {
        // A saved bike always starts parked, including after a disconnect or crash.
        speed = 0; verticalSpeed = 0;
    }
    @Override protected void addAdditionalSaveData(CompoundTag tag) { tag.putInt("ZionVehicleVersion", 1); }
    @Override public boolean isPickable() { return true; }
    @Override public boolean isPushable() { return false; }
    @Override public boolean canBeCollidedWith() { return !isRemoved(); }
    @Override protected boolean canAddPassenger(Entity passenger) { return getPassengers().isEmpty() && passenger instanceof Player; }
    // Null intentionally keeps the server authoritative; input is read from the first passenger.
    @Override public LivingEntity getControllingPassenger() { return null; }
    public float speedMph() { return entityData.get(SPEED); }
    @Override public InteractionResult interact(Player player, InteractionHand hand) {
        if (player.isSecondaryUseActive()) return InteractionResult.PASS;
        if (!level().isClientSide && player.startRiding(this)) {
            player.displayClientMessage(Component.literal("Yoda is driving with you! W: go · S: brake · A/D: turn · hold Space: turbo · Shift: get off"), false);
        }
        return InteractionResult.SUCCESS;
    }
    @Override public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.getEntity() instanceof Player player && player.isCreative() && !isVehicle()) { discard(); return true; }
        return false;
    }
    @Override protected void removePassenger(Entity passenger) { super.removePassenger(passenger); speed = 0; setDeltaMovement(Vec3.ZERO); }
    @Override protected void positionRider(Entity passenger, MoveFunction move) {
        if (!hasPassenger(passenger)) return;
        double radians = Math.toRadians(getYRot());
        // Yoda occupies the front saddle; the player has the comfortable rear seat.
        move.accept(passenger, getX() + Math.sin(radians) * .55, getY() + .87, getZ() - Math.cos(radians) * .55);
        passenger.fallDistance = 0;
    }
    @Override public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
        for (int y = 0; y <= 2; y++) for (int side : new int[]{1, -1}) {
            double r = Math.toRadians(getYRot());
            Vec3 p = new Vec3(getX() + Math.cos(r) * side * 1.25, getY() + y, getZ() + Math.sin(r) * side * 1.25);
            if (level().hasChunkAt(BlockPos.containing(p)) && level().noCollision(passenger, passenger.getBoundingBox().move(p.subtract(passenger.position())))) return p;
        }
        return position().add(0, 2, 0);
    }
    @Override public void lerpTo(double x, double y, double z, float yaw, float pitch, int steps) {
        lerpX=x; lerpY=y; lerpZ=z; lerpYaw=yaw; lerpSteps=Math.max(1, Math.min(steps, 3));
    }
    @Override public void tick() {
        super.tick();
        if (level().isClientSide) {
            if (lerpSteps > 0) {
                setPos(getX()+(lerpX-getX())/lerpSteps, getY()+(lerpY-getY())/lerpSteps, getZ()+(lerpZ-getZ())/lerpSteps);
                setYRot(getYRot()+Mth.wrapDegrees(lerpYaw-getYRot())/lerpSteps); lerpSteps--;
            }
            return;
        }
        Input input = getFirstPassenger() instanceof ServerPlayer rider ? rider.getLastClientInput() : Input.EMPTY;
        boolean driving = getFirstPassenger() instanceof ServerPlayer;
        boolean turbo = input.jump() && input.forward() && driving;
        double target = driving && input.forward() ? (turbo ? TURBO_BLOCKS_PER_TICK : CRUISE_BLOCKS_PER_TICK) : 0;
        if (input.backward() || !driving) target = 0;
        double acceleration = turbo ? .32 : .08;
        speed = approach(speed, target, target < speed ? 1.2 : acceleration);
        float turn = (input.left() ? 1 : 0) - (input.right() ? 1 : 0);
        // Tight turns would otherwise cross an entire chunk in one frame at turbo speed.
        setYRot(getYRot() - turn * (float)(4.0 / (1.0 + speed * .6)));
        verticalSpeed = Math.max(-1.5, verticalSpeed - .08);
        double radians = Math.toRadians(getYRot());
        Vec3 requested = new Vec3(-Math.sin(radians)*speed, verticalSpeed, Math.cos(radians)*speed);
        Vec3 start = position();
        safetyBrake = false;
        int steps = Math.max(1, (int)Math.ceil(requested.length()/SUBSTEP));
        Vec3 step = requested.scale(1.0 / steps);
        // The 1,000 mph cap yields at most 90 bounded collision checks per server tick.
        for (int i=0; i<steps; i++) {
            AABB next = getBoundingBox().expandTowards(step).inflate(.02);
            if (!loaded(next) || !level().getWorldBorder().isWithinBounds(next)) { safetyBrake=true; break; }
            Vec3 before = position();
            move(MoverType.SELF, step);
            if (verticalCollision) verticalSpeed=0;
            Vec3 actual = position().subtract(before);
            if (Math.abs(actual.x-step.x) > 1.0e-5 || Math.abs(actual.z-step.z) > 1.0e-5) { safetyBrake=true; break; }
        }
        if (safetyBrake) speed=0;
        Vec3 actual = position().subtract(start);
        // Zero velocity prevents vanilla client prediction from adding movement twice.
        setDeltaMovement(Vec3.ZERO);
        entityData.set(SPEED, (float)(actual.horizontalDistance()*20/0.44704));
        hasImpulse=true;
        fallDistance=0;
        if (tickCount % 5 == 0 && getFirstPassenger() instanceof ServerPlayer player) {
            String message = String.format(java.util.Locale.ROOT, "Yoda's rainbow motorcycle · %.0f mph%s", speedMph(), safetyBrake ? " · Safety brake: obstacle or unloaded road" : turbo ? " · TURBO target 1,000 mph" : " · Hold Space + W for TURBO");
            player.displayClientMessage(Component.literal(message), true);
        }
    }
    private boolean loaded(AABB box) {
        int minX=Mth.floor(box.minX)>>4, maxX=Mth.floor(box.maxX)>>4;
        int minZ=Mth.floor(box.minZ)>>4, maxZ=Mth.floor(box.maxZ)>>4;
        for (int x=minX;x<=maxX;x++) for(int z=minZ;z<=maxZ;z++) if (!level().hasChunk(x,z)) return false;
        return true;
    }
    public static double approach(double value, double target, double delta) {
        return value < target ? Math.min(target, value+delta) : Math.max(target, value-delta);
    }
}
