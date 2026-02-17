import bpy

def add_node_group_options(self, context):
    layout = self.layout
        
    if context.active_node and (context.active_node.bl_idname == 'GeometryNodeGroup' or context.active_node.bl_idname == 'ShaderNodeGroup' or context.active_node.bl_idname == 'CompositorNodeGroup'):
        layout.separator()
        layout.operator("node.set_default_values", text="Set Default Values", icon='SORT_ASC')
        layout.operator("node.reset_default_values", text="Reset to Default Values", icon='LOOP_BACK')

class SetDefaultValues(bpy.types.Operator):
    """Set the default values of the selected node group to the current values of its input sockets"""
    bl_idname = "node.set_default_values"
    bl_label = "Set Default Values"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_active = context.active_node
        node_tree = node_active.node_tree

        for item in node_tree.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                try:
                    socket = node_active.inputs.get(item.identifier)
                    if socket:
                        item.default_value = socket.default_value
                except Exception as e:
                    print(f"Error setting default value for {item.identifier}: {e}")
                    pass
            
        self.report({'INFO'}, f"Successfully set {node_tree.name}")
        return {'FINISHED'}

class ResetDefaultValues(bpy.types.Operator):
    """Reset the values of the input sockets of the selected node group to their default values"""
    bl_idname = "node.reset_default_values"
    bl_label = "Reset Default Values"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node is not None and node.bl_idname in {
            'GeometryNodeGroup', 'ShaderNodeGroup', 'CompositorNodeGroup'
        }

    def execute(self, context):
        node_active = context.active_node
        node_tree = node_active.node_tree

        for item in node_tree.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                try:
                    socket = node_active.inputs.get(item.identifier)
                    if socket:
                        socket.default_value = item.default_value
                except Exception as e:
                    print(f"Error resetting default value for {item.identifier}: {e}")
                    pass
                
        self.report({'INFO'}, f"Successfully reset {node_tree.name}")

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SetDefaultValues)
    bpy.utils.register_class(ResetDefaultValues)
    bpy.types.NODE_MT_context_menu.append(add_node_group_options)

    # Assign the ResetDefaultValues operator to the Backspace key
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    kmi = km.keymap_items.new("node.reset_default_values", 'BACK_SPACE', 'PRESS')

def unregister():
    bpy.utils.unregister_class(SetDefaultValues)
    bpy.utils.unregister_class(ResetDefaultValues)
    bpy.types.NODE_MT_context_menu.remove(add_node_group_options)

    # Remove the keymap item
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get("Node Editor")
    if km:
        for kmi in km.keymap_items:
            if kmi.idname == "node.reset_default_values":
                km.keymap_items.remove(kmi)
                break

if __name__ == "__main__":
    register()
