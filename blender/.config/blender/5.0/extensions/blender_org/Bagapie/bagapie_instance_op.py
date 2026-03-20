import bpy
from bpy.types import Operator
from . presets import bagapieModifiers
from .utils import get_or_create_collection,Get_addon_pref

class BAGAPIE_OT_makereal(Operator):
    """ Make Instances real """
    bl_idname = "bagapie.makereal"
    bl_label = 'Make Real'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'EMPTY'
        )
    
    index: bpy.props.IntProperty(default=0) # type: ignore
    
    def execute(self, context):
        empty_name = bpy.context.active_object.name
        bpy.ops.object.duplicates_make_real()
        target = bpy.context.selected_objects
        for targ in target:
            try:
                targ["bagapie"]
            except:
                targ["bagapie"] = None

            if targ["bagapie"] is not None:
                bpy.data.objects.remove(targ)
            else:
                del targ["bagapie"]

        empty = bpy.data.objects[empty_name]
        bpy.data.objects.remove(empty)

        return {'FINISHED'}

class BAGAPIE_OT_instance(Operator):
    """Turn Group into instances. The group is moved to the world origin and replaced by an instance"""
    bl_idname = 'bagapie.instance'
    bl_label = bagapieModifiers['instance']['label']
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.object

        return (
            o is not None and 
            o.type == 'MESH'
        )

    def execute(self, context):
        target = bpy.context.active_object

        # COLLECTION        
        main_coll = get_or_create_collection("BagaPie")
        manage_coll = get_or_create_collection("BagaPie_Manage", main_coll)
        instances_coll = get_or_create_collection("BagaPie_Instances", manage_coll)

        # SET ORIGIN
        for mo in target.modifiers:
            if mo.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
                coll_gr = mo['Socket_0']
                bpy.ops.object.collection_instance_add(collection= mo['Socket_0'].name , align='WORLD', location=target.location)

            for o in coll_gr.objects:
                o.hide_select = False
                find_sub_group(o,coll_gr) # Recursive loop in case there is group in group in group ...

        target.location = (0, 0, 0)

        # Move instance to bagapie collections
        instance = bpy.context.active_object
        instance["bagapie"]="BagaPie_group_instance"
        current_coll = instance.users_collection
        current_coll[0].objects.unlink(instance)
        instances_coll.objects.link(instance)

        bagapie_pref = Get_addon_pref()
        if bagapie_pref.alpha_tool == True:
            bpy.ops.bagapie.double_click_edit("INVOKE_DEFAULT")

        return {'FINISHED'}

def is_a_box(obj):
    if obj is not None:
        if obj.type == 'MESH':
            for mo in obj.modifiers:
                if mo.type == 'NODES':
                    if mo.node_group.name.startswith('BagaPie_Group_Bounding_Box'):
                        return True
    return False

def link_to_coll(ob,coll):
    if ob.name not in coll.objects:
        coll.objects.link(ob)

def find_sub_group(obj,coll):
    if is_a_box(obj) == True:
        for ob in obj.children:
            link_to_coll(ob,coll)
            find_sub_group(ob,coll)

classes = [
    BAGAPIE_OT_makereal,
    BAGAPIE_OT_instance
]