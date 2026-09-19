"""Deterministic JSON geometry and game resources. Does not generate raster artwork."""
import json
from pathlib import Path

ROOT = Path(__file__).parent / 'src/main/resources'
ASSETS = ROOT / 'assets/zion_showcase'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def part(bounds, texture):
    return {'from':bounds[:3], 'to':bounds[3:], 'faces':{side:{'texture':'#'+texture} for side in ('north','south','east','west','up','down')}}

models = {
 'fridge': [('white',[1,0,2,15,16,15]),('door',[1,0,1,15,11,2]),('door',[1,11.5,1,15,16,2]),('metal',[2,3,0,3,9,1]),('metal',[2,12.5,0,3,15,1]),('dark',[1,11,1,15,11.5,2])],
 'grill': [('dark',[1,9,1,15,12,15]),('metal',[1,12,1,15,13,15]),('metal',[2,0,2,4,9,4]),('metal',[12,0,2,14,9,4]),('metal',[2,0,12,4,9,14]),('metal',[12,0,12,14,9,14])]+[('dark',[x,13,2,x+.5,13.3,14]) for x in range(2,15,2)],
 'stove': [('white',[1,0,1,15,14,15]),('metal',[0,14,0,16,15,16]),('dark',[2,15,2,6,15.5,6]),('dark',[10,15,2,14,15.5,6]),('dark',[2,15,10,6,15.5,14]),('dark',[10,15,10,14,15.5,14]),('dark',[3,4,.5,13,10,1]),('metal',[3,11,0,13,12,1])],
 'oven': [('metal',[1,0,1,15,14,15]),('white',[0,14,0,16,16,16]),('dark',[2,2,.5,14,11,1]),('glass',[3,3,0,13,9,.5]),('metal',[3,11,0,13,12,1]),('dark',[3,13,0,5,14,1]),('dark',[11,13,0,13,14,1])],
 'bookshelf': [('wood',[0,0,12,16,16,16]),('wood',[0,0,2,2,16,12]),('wood',[14,0,2,16,16,12]),('wood',[0,0,2,16,2,16]),('wood',[0,7,2,16,9,16]),('wood',[0,14,2,16,16,16])]+[(color,[x,y,5,x+1.5,y+4.7,11]) for y in (2,9) for x,color in zip(range(3,14,2),('red','blue','green','gold','purple','blue'))],
 'chair': [('wood',[2,6,2,14,8,14]),('blue',[2,8,2,14,9,14]),('wood',[2,9,13,14,16,15]),('blue',[3,10,12,13,15,13])]+[('wood',[x,0,z,x+2,6,z+2]) for x in (2,12) for z in (2,12)],
 'sofa': [('wood',[2,0,2,4,2,4]),('wood',[12,0,2,14,2,4]),('wood',[2,0,12,4,2,14]),('wood',[12,0,12,14,2,14]),('blue',[1,2,1,15,6,15]),('blue',[0,5,2,3,12,16]),('blue',[13,5,2,16,12,16]),('blue',[0,8,12,16,16,16]),('soft',[3,6,1,8,9,12]),('soft',[8.1,6,1,13,9,12]),('soft',[3,9,11,13,14,12])],
 'sink': [('wood',[1,0,2,15,10,15]),('white',[0,10,1,16,11,16]),('white',[0,11,1,3,13,16]),('white',[13,11,1,16,13,16]),('white',[3,11,1,13,13,3]),('white',[3,11,12,13,13,16]),('metal',[7,13,13,9,16,14]),('metal',[7,15,10,9,16,14]),('water',[3,11,3,13,11.2,12])],
 'toilet': [('white',[4,0,4,12,4,13]),('white',[2,4,2,14,6,13]),('white',[2,6,1,4,8,13]),('white',[12,6,1,14,8,13]),('white',[4,6,1,12,8,3]),('white',[4,6,11,12,8,13]),('white',[2,0,12,14,15,16]),('white',[1.5,15,11.5,14.5,16,16]),('metal',[10,13,11.5,13,14,12]),('water',[4,6.1,3,12,6.3,11])],
 'shower': [('white',[0,0,0,16,2,16]),('glass',[0,2,0,1,16,14]),('white',[0,2,14,16,16,16]),('metal',[7,2,13,9,15,14]),('metal',[6,14,9,10,15,14]),('dark',[6,1.9,6,10,2.1,10])],
}
textures = {'white':'quartz_block_side','door':'white_concrete','metal':'iron_block','dark':'black_concrete','glass':'light_blue_stained_glass','wood':'oak_planks','blue':'cyan_wool','soft':'light_blue_wool','water':'blue_stained_glass','red':'red_concrete','green':'lime_concrete','gold':'yellow_concrete','purple':'purple_concrete'}
lang={'item.zion_showcase.shiny_sword':'Zion’s Shiny Sword','item.zion_showcase.rainbow_motorcycle':'Yoda’s Rainbow Motorcycle','entity.zion_showcase.rainbow_motorcycle':'Yoda’s Rainbow Motorcycle'}
for name, elements in models.items():
    write(ASSETS / 'models/block' / (name+'.json'), {'ambientocclusion':True,'textures':{**{k:'minecraft:block/'+v for k,v in textures.items()},'particle':'minecraft:block/quartz_block_side'},'elements':[part(bounds,texture) for texture,bounds in elements]})
    write(ASSETS / 'blockstates' / (name+'.json'), {'variants':{f'facing={direction}':{'model':f'zion_showcase:block/{name}','y':rotation} for direction,rotation in [('north',0),('east',90),('south',180),('west',270)]}})
    write(ASSETS / 'models/item' / (name+'.json'), {'parent':f'zion_showcase:block/{name}','display':{'gui':{'rotation':[30,225,0],'translation':[0,0,0],'scale':[.65,.65,.65]},'ground':{'translation':[0,3,0],'scale':[.25,.25,.25]},'fixed':{'rotation':[0,180,0],'scale':[.5,.5,.5]},'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.375,.375,.375]}}})
    write(ROOT/'data/zion_showcase/loot_table/blocks'/(name+'.json'), {'type':'minecraft:block','pools':[{'rolls':1,'entries':[{'type':'minecraft:item','name':f'zion_showcase:{name}'}],'conditions':[{'condition':'minecraft:survives_explosion'}]}]})
    lang['block.zion_showcase.'+name]=name.replace('_',' ').title()
for name in [*models,'shiny_sword','rainbow_motorcycle']:
    write(ASSETS/'items'/(name+'.json'),{'model':{'type':'minecraft:model','model':f'zion_showcase:item/{name}'}})
for name in ('shiny_sword','rainbow_motorcycle'):
    write(ASSETS/'models/item'/(name+'.json'),{'parent':'minecraft:item/'+('handheld' if name=='shiny_sword' else 'generated'),'textures':{'layer0':f'zion_showcase:item/{name}'}})
write(ASSETS/'lang/en_us.json',lang)
write(ROOT/'data/minecraft/tags/block/mineable/pickaxe.json', {'replace':False,'values':['zion_showcase:'+n for n in models]})
write(ROOT/'data/zion_showcase/recipe/shiny_sword.json', {'type':'minecraft:crafting_shaped','category':'equipment','pattern':[' D ',' D ',' S '],'key':{'D':'minecraft:diamond','S':'minecraft:stick'},'result':{'id':'zion_showcase:shiny_sword','count':1}})
write(ROOT/'data/zion_showcase/recipe/rainbow_motorcycle.json', {'type':'minecraft:crafting_shaped','category':'equipment','pattern':[' R ','ISI','B B'],'key':{'R':'minecraft:redstone','I':'minecraft:iron_ingot','S':'minecraft:saddle','B':'minecraft:black_wool'},'result':{'id':'zion_showcase:rainbow_motorcycle','count':1}})

if __name__ == '__main__':
    print(f'Wrote geometry and Minecraft 1.21.4 resources for {len(models)} furniture blocks and 2 items.')
