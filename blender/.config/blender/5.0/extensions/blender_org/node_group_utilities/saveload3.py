import bpy

def add_node_group_options(self, context):
    layout = self.layout
    
    if context.active_node and context.active_node.bl_idname == 'ShaderNodeGroup':
        layout.separator()
        layout.operator("node.add_label", text="Add Label")
        
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

        for input_socket, output_socket in zip(node_active.inputs, node_active.node_tree.inputs):
            try:
                output_socket.default_value = input_socket.default_value
            except:
                pass
            
        self.report({'INFO'}, "Default values set")
        return {'FINISHED'}


class ResetDefaultValues(bpy.types.Operator):
    """Reset the values of the input sockets of the selected node group to their default values"""
    bl_idname = "node.reset_default_values"
    bl_label = "Reset Default Values"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_active = context.active_node

        for input_socket, output_socket in zip(node_active.inputs, node_active.node_tree.inputs):
            try:
                input_socket.default_value = output_socket.default_value
            except:
                pass

        return {'FINISHED'}
        

class AddLabel(bpy.types.Operator):
    """Add a label to the selected node group"""
    bl_idname = "node.add_label"
    bl_label = "Label Name"
    bl_options = {'REGISTER', 'UNDO'}
    socket_name: bpy.props.StringProperty(name="", default="")
    label_style: bpy.props.EnumProperty(
        name="Accessory",
        items=[
            ('PLUS', 'Pluses', ''  , "", 3),
            ('EQUAL', 'Equals', '' , "", 4),
            ('DASH', 'Dashes', '' , "", 5),
            ('LINES', 'Vertical bars', '' , "", 6),
            ('UNDERSCORE', 'Underscores', '' , "", 7),
            ('TRI', 'Triangle', '' , "", 8),
            ('BULLET', 'Bullet', '' , "", 9),
            ('DIAMOND', 'Diamond', '' , "", 10),
            ('BLOCK', 'Blocks', '' , "", 11),
            ('ANGLE', 'Angle Brackets', '' , "", 12),
            ('NONE', 'None', '' , "PANEL_CLOSE", 1),
            ('CUSTOM', 'Custom', "" , "GREASEPENCIL", 2),
        ],
        default='NONE',
    )

    uppercase: bpy.props.BoolProperty(name="UPPERCASE", default=True)
    custom_prefix: bpy.props.StringProperty(name="Prefix", default="")
    custom_suffix: bpy.props.StringProperty(name="Suffix", default="")

    def execute(self, context):
        node_active = context.active_node
        node_tree = node_active.node_tree
        
        if self.socket_name == "":
            return self.invoke_popup(context)

        socket_name = self.socket_name.strip() #Remove Spaces
        label_text = socket_name.upper() if self.uppercase else socket_name

        if self.label_style == 'PLUS':
            label_text = "+++++ " + label_text + " +++++"
        elif self.label_style == 'EQUAL':
            label_text = "====[ " + label_text + " ]===="
        elif self.label_style == 'DASH':
            label_text = "----- " + label_text + " -----"
        elif self.label_style == 'LINES':
            label_text = "||||| " + label_text + " |||||"
        elif self.label_style == 'UNDERSCORE':
            label_text = "_____ " + label_text + " _____"
        elif self.label_style == 'TRI':
            label_text = "► " + label_text
        elif self.label_style == 'BULLET':
            label_text = "● " + label_text
        elif self.label_style == 'DIAMOND':
            label_text = "❖ " + label_text
        elif self.label_style == 'ANGLE':
            label_text = "< " + label_text + " >"
        elif self.label_style == 'BLOCK':
            label_text = "██ " + label_text + " ██"
        elif self.label_style == 'CUSTOM':
            label_text = self.custom_prefix + " " + label_text + " " + self.custom_suffix
        else:
            label_text = label_text

        node_tree.inputs.new('NodeSocketString', label_text)
        node_tree.inputs[-1].hide_value = True

        self.report({'INFO'}, 'Added {} Label'.format(self.socket_name))
        self.socket_name = ""
        return {'FINISHED'}

    def invoke_popup(self, context, event=None):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "socket_name")
        layout.prop(self, "label_style")
        
        if self.label_style == 'CUSTOM':  # Add this block
            layout.prop(self, "custom_prefix")
            layout.prop(self, "custom_suffix")

        layout.prop(self, "uppercase")

      
def register():
    bpy.utils.register_class(AddLabel)  
    bpy.utils.register_class(SetDefaultValues)
    bpy.utils.register_class(ResetDefaultValues)
    bpy.types.NODE_MT_context_menu.append(add_node_group_options)

def unregister():
    bpy.utils.unregister_class(AddLabel)  
    bpy.utils.unregister_class(SetDefaultValues)
    bpy.utils.unregister_class(ResetDefaultValues)
    bpy.types.NODE_MT_context_menu.remove(add_node_group_options)

if __name__ == "__main__":
    register()
