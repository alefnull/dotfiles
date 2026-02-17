import bpy
import os

addon_dir = os.path.dirname(__file__)
blendFilePath = os.path.join(addon_dir, "socketmaker.blend")

class SocketMakerOperator(bpy.types.Operator):
    """A dummy node to help you add custom sockets to your node groups"""
    bl_idname = "node.add_socketmaker"
    bl_label = "Add Socket Maker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        nodeGroupName = "SocketMaker"

        try:
            latestNodeGroupName = max((nodeGroup.name for nodeGroup in bpy.data.node_groups if nodeGroupName in nodeGroup.name), key=lambda name: int(name.split('.')[-1]) if name.split('.')[-1].isdigit() else -1)
        except:
            with bpy.data.libraries.load(blendFilePath) as (dataFrom, dataTo):
                dataTo.node_groups = [name for name in dataFrom.node_groups if nodeGroupName == name]
            
            latestNodeGroupName = max((nodeGroup.name for nodeGroup in bpy.data.node_groups if nodeGroupName in nodeGroup.name), key=lambda name: int(name.split('.')[-1]) if name.split('.')[-1].isdigit() else -1)
        

        bpy.ops.node.add_node(type="ShaderNodeGroup")
        node = context.selected_nodes[0]
        node.node_tree = bpy.data.node_groups[latestNodeGroupName]
        #node.location = context.space_data.cursor_location
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
       
        return {'FINISHED'}

def draw_func(self, context):
    if context.area.ui_type == 'ShaderNodeTree':
        self.layout.operator_context = 'INVOKE_DEFAULT'
        self.layout.operator(SocketMakerOperator.bl_idname, text="Socket Maker")

def register():
    bpy.utils.register_class(SocketMakerOperator)
    bpy.types.NODE_MT_add.append(draw_func)

def unregister():
    bpy.utils.unregister_class(SocketMakerOperator)
    bpy.types.NODE_MT_add.remove(draw_func)

if __name__ == "__main__":
    register()


