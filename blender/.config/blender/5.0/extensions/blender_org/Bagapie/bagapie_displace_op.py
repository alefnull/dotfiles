import bpy
import json
from bpy.types import Operator
from . presets import bagapieModifiers

class BAGAPIE_OT_displace_remove(Operator):
    """Remove Bagapie Displace modifiers"""
    bl_idname = "bagapie.displace_remove"
    bl_label = 'Remove Bagapie Displace'

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        try:
            modifiers = val['modifiers']
            avoid_string = "BagaPie_Texture"

            for mod in modifiers:
                if mod.startswith("Baga") and not mod.startswith(avoid_string):
                    obj.modifiers.remove(obj.modifiers[mod])
        except:
            print("Some elements (modifier or objects) were missing.")
        
        context.object.bagapieList.remove(self.index)
        if len(obj.bagapieList) <= obj.bagapieIndex and obj.bagapieIndex != 0:
            obj.bagapieIndex -= 1

        return {'FINISHED'}

class BAGAPIE_OT_displace(Operator):
    """Add displacement with texture and subdivision on the selected object"""
    bl_idname = 'wm.displace'
    bl_label = bagapieModifiers['displace']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    dir: bpy.props.EnumProperty(
        name="Dirrection",
        items=[('X', "X",""),
               ('Y', "Y",""),
               ('Z', "Z",""),
               ('NORMAL', "Normal",""),
               ('CUSTOM_NORMAL', "Custom Normal",""),
               ('RGB_TO_XYZ', "RGB to XYZ","")
               ],
        default='NORMAL'
    ) # type: ignore
    str: bpy.props.FloatProperty(
        name="Strength",
        default=1,
        min=-100,
        max=100,
    ) # type: ignore
    mid: bpy.props.FloatProperty(
        name="Midlevel",
        default=0.5,
        min=0,
        max=1,
    ) # type: ignore
    # ADD TEXTURE
    disp_tex_type: bpy.props.EnumProperty(
        name="Texture Type",
        items=[('BLEND', "Blend",""),
               ('CLOUDS', "Clouds",""),
               ('DISTORTED_NOISE', "Distorted Noise",""),
               ('MAGIC', "Magic",""),
               ('MARBLE', "Marble",""),
               ('MUSGRAVE', "Musgrave",""),
               ('NOISE', "Noise",""),
               ('STUCCI', "Stucci",""),
               ('VORONOI', "Voronoi",""),
               ('WOOD', "Wood","")
               ],
        default='MUSGRAVE'
    ) # type: ignore
    disp_tex_mapping: bpy.props.EnumProperty(
        name="Texture Mapping",
        items=[('LOCAL', "Local",""),
               ('GLOBAL', "Global",""),
               ('OBJECT', "Object",""),
               ('UV', "UV","")
               ],
        default='LOCAL',
    ) # type: ignore
    disp_tex_size: bpy.props.FloatProperty(name="Texture Scale", default=0.5, min=0, soft_max=30) # type: ignore
    disp_tex_rampmin: bpy.props.FloatProperty(name="ColorRamp Min", default=0, min=0, max=1) # type: ignore
    disp_tex_rampmax: bpy.props.FloatProperty(name="ColorRamp Max", default=1, min=0, max=1) # type: ignore
    tex_type_A = ('CLOUDS','DISTORTED_NOISE','MARBLE','MUSGRAVE','STUCCI','VORONOI')

    # SUBDIVISION SURFACE
    disp_use_simplesub: bpy.props.BoolProperty(name="Simple Subdivision", default=False) # type: ignore
    disp_sub_count: bpy.props.IntProperty(name="Subdiv Count", default=2, min=1, max=6) # type: ignore

    def execute(self, context):
        target = bpy.context.active_object
        new = bpy.data.objects[target.name].modifiers.new

        subdiv = new(name='BagaSubdiv', type='SUBSURF')
        subdiv.levels = self.disp_sub_count
        subdiv.render_levels = self.disp_sub_count
        if self.disp_use_simplesub is True:
            subdiv.subdivision_type = 'SIMPLE'

        displace = new(name='BagaDisplace', type='DISPLACE')
        displace.direction = self.dir
        displace.strength = self.str
        displace.mid_level = self.mid

        texture = bpy.data.textures.new(name="BagaPie_Texture", type=self.disp_tex_type)
        if self.disp_tex_type in self.tex_type_A:
            texture.noise_scale = self.disp_tex_size
            texture.use_color_ramp = True
            texture.color_ramp.elements[0].position = self.disp_tex_rampmin
            texture.color_ramp.elements[1].position = self.disp_tex_rampmax
        displace.texture = texture
        displace.texture_coords = self.disp_tex_mapping

    # CUSTOM PROPERTIES
        val = {
              'name': 'displace',
              'modifiers':[
                          subdiv.name,
                          displace.name,
                          texture.name,
                          ]
        }

        item = target.bagapieList.add()
        item.val = json.dumps(val)
        target.bagapieIndex = len(target.bagapieList)-1
        
        return {'FINISHED'}
    
classes = [
    BAGAPIE_OT_displace_remove,
    BAGAPIE_OT_displace
]