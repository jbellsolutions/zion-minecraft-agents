package com.zion.showcase;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.*;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.*;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.entity.*;
import net.minecraft.world.level.block.state.*;
import net.minecraft.world.level.block.state.properties.*;
import net.minecraft.world.phys.*;
import net.minecraft.world.phys.shapes.*;

public final class FurnitureBlock extends Block implements EntityBlock {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
    public static final BooleanProperty LIT = BlockStateProperties.LIT;
    private final String kind;
    private final VoxelShape[] shapes = new VoxelShape[4];
    public FurnitureBlock(String kind, Properties properties) {
        super(properties); this.kind=kind;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(LIT, false));
        shapes[0]=shape(kind);
        for (int i=1;i<4;i++) shapes[i]=rotate(shapes[i-1]);
    }
    public String kind() { return kind; }
    public boolean storage() { return kind.equals("fridge") || kind.equals("bookshelf"); }
    public boolean cooking() { return List.of("grill", "stove", "oven").contains(kind); }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING, LIT); }
    @Override public BlockState getStateForPlacement(BlockPlaceContext ctx) { return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite()); }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) { return state.setValue(FACING, rotation.rotate(state.getValue(FACING))); }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) { return state.rotate(mirror.getRotation(state.getValue(FACING))); }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return shapes[switch(state.getValue(FACING)) { case EAST -> 1; case SOUTH -> 2; case WEST -> 3; default -> 0; }];
    }
    @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return storage() ? new StorageFurniture(pos, state) : cooking() ? new CookingFurniture(pos, state) : null;
    }
    @Override @SuppressWarnings("unchecked") public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (cooking() && !level.isClientSide && type == Showcase.COOKING.get())
            return (l,p,s,be) -> AbstractFurnaceBlockEntity.serverTick((ServerLevel)l, p, s, (CookingFurniture)be);
        return null;
    }
    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (level.getBlockEntity(pos) instanceof MenuProvider menu) {
            player.openMenu(menu);
            level.playSound(null, pos, SoundEvents.IRON_TRAPDOOR_OPEN, SoundSource.BLOCKS, .5f, .8f);
        } else if (kind.equals("chair") || kind.equals("sofa") || kind.equals("toilet")) {
            List<ArmorStand> seats = level.getEntitiesOfClass(ArmorStand.class, new AABB(pos).inflate(.1), e -> e.getTags().contains("zion_furniture_seat"));
            ArmorStand seat = seats.isEmpty() ? new ArmorStand(EntityType.ARMOR_STAND, level) : seats.get(0);
            if (!seat.getPassengers().isEmpty()) return InteractionResult.FAIL;
            if (seats.isEmpty()) {
                seat.setPos(pos.getX()+.5, pos.getY()+.30, pos.getZ()+.5);
                seat.setInvisible(true); seat.setNoGravity(true); seat.setInvulnerable(true); seat.setNoBasePlate(true);
                var seatData=new net.minecraft.nbt.CompoundTag(); seatData.putBoolean("Small",true); seatData.putBoolean("Marker",true); seat.readAdditionalSaveData(seatData);
                seat.addTag("zion_furniture_seat");
                seat.getPersistentData().putLong("Furniture", pos.asLong());
                level.addFreshEntity(seat);
            }
            player.startRiding(seat);
        } else {
            // Water stays inside the fixture: particles and sound never place flowing water blocks.
            ((ServerLevel)level).sendParticles(ParticleTypes.SPLASH, pos.getX()+.5, pos.getY()+(kind.equals("shower")?1.8:.8), pos.getZ()+.5, 24, .18, .2, .18, .04);
            level.playSound(null, pos, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, .7f, 1.25f);
        }
        return InteractionResult.SUCCESS;
    }
    @Override protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState replacement, boolean moving) {
        if (!state.is(replacement.getBlock())) {
            if (level.getBlockEntity(pos) instanceof Container container) {
                Containers.dropContents(level, pos, container);
                if (level instanceof ServerLevel server && container instanceof CookingFurniture cooking) {
                    cooking.getRecipesToAwardAndPopExperience(server, Vec3.atCenterOf(pos));
                }
                level.updateNeighbourForOutputSignal(pos, this);
            }
            for (ArmorStand seat : level.getEntitiesOfClass(ArmorStand.class, new AABB(pos).inflate(.1), e -> e.getTags().contains("zion_furniture_seat"))) { seat.ejectPassengers(); seat.discard(); }
        }
        super.onRemove(state, level, pos, replacement, moving);
    }
    @Override public void animateTick(BlockState state, Level level, BlockPos pos, net.minecraft.util.RandomSource random) {
        if (cooking() && state.getValue(LIT)) {
            level.addParticle(ParticleTypes.SMOKE, pos.getX()+.5, pos.getY()+1.05, pos.getZ()+.5, 0, .03, 0);
            level.addParticle(ParticleTypes.FLAME, pos.getX()+.5, pos.getY()+.8, pos.getZ()+.5, 0, 0, 0);
        }
    }
    private static VoxelShape shape(String kind) {
        return switch (kind) {
            case "fridge" -> union(box(1,0,2,15,16,15), box(2,0,0,3,13,2));
            case "bookshelf" -> union(box(0,0,12,16,16,16), box(0,0,2,2,16,12), box(14,0,2,16,16,12), box(0,0,2,16,2,16), box(0,7,2,16,9,16), box(0,14,2,16,16,16));
            case "chair" -> union(box(2,6,2,14,9,14), box(2,9,12,14,16,15), box(2,0,2,4,6,4), box(12,0,2,14,6,4), box(2,0,12,4,6,14), box(12,0,12,14,6,14));
            case "sofa" -> union(box(1,2,1,15,8,15), box(0,5,2,3,12,16), box(13,5,2,16,12,16), box(0,8,12,16,16,16));
            case "grill" -> union(box(1,9,1,15,13,15), box(2,0,2,4,9,4), box(12,0,2,14,9,4), box(2,0,12,4,9,14), box(12,0,12,14,9,14));
            case "sink" -> union(box(1,0,2,15,10,15), box(0,10,1,16,13,16), box(7,13,12,9,16,14));
            case "toilet" -> union(box(4,0,4,12,4,13), box(2,4,1,14,8,13), box(2,0,12,14,16,16));
            case "shower" -> union(box(0,0,0,16,2,16), box(0,2,14,16,16,16), box(0,2,0,1,16,14));
            default -> union(box(1,0,1,15,14,15), box(0,14,0,16,16,16));
        };
    }
    private static VoxelShape union(VoxelShape... parts) { VoxelShape result=Shapes.empty(); for(var part:parts) result=Shapes.or(result,part); return result; }
    private static VoxelShape rotate(VoxelShape shape) {
        final VoxelShape[] out={Shapes.empty()};
        shape.forAllBoxes((a,b,c,d,e,f)->out[0]=Shapes.or(out[0],Shapes.box(1-f,b,a,1-c,e,d)));
        return out[0];
    }
}
