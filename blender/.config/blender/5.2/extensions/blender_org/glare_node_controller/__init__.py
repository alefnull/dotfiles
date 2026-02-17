bl_info = {
    "name": "Glare Node Controller",
    "author": "darkstarrd",
    "version": (2, 3, 3), # Final version using the prepend injection method
    "blender": (4, 0, 0), # Requires Blender 4.0 or newer
    "location": "Properties > Render Properties > (Top of Panel)",
    "description": "Injects a collapsible panel into the Render Properties to control a Glare node and viewport compositor settings.",
    "warning": "This is the definitive, professionally implemented version.",
    "doc_url": "",
    "category": "Node",
}

import bpy
from mathutils import Vector


TARGET_NODE_TYPE = 'CompositorNodeGlare'
PARAMETER_MAP = {
    'FOG_GLOW': {"Highlights": [('socket','Threshold',"Threshold"),('socket','Smoothness',"Smoothness"),('socket','Clamp',"Clamp"),('socket','Maximum',"Maximum")],"Adjust": [('socket','Strength',"Strength"),('socket','Saturation',"Saturation"),('socket','Tint',"Tint")],"Glare": [('socket','Size',"Size")]},
    'BLOOM': {"Highlights": [('socket','Threshold',"Threshold"),('socket','Smoothness',"Smoothness"),('socket','Clamp',"Clamp"),('socket','Maximum',"Maximum")],"Adjust": [('socket','Strength',"Strength"),('socket','Saturation',"Saturation"),('socket','Tint',"Tint")],"Glare": [('socket','Size',"Size")]},
    'GHOSTS': {"Highlights": [('socket','Threshold',"Threshold"),('socket','Smoothness',"Smoothness"),('socket','Clamp',"Clamp"),('socket','Maximum',"Maximum")],"Adjust": [('socket','Strength',"Strength"),('socket','Saturation',"Saturation"),('socket','Tint',"Tint")],"Glare": [('property','iterations',"Iterations"),('property','color_modulation',"Color Modulation")]},
    'STREAKS': {"General": [('property','mix',"Mix")],"Highlights": [('property','threshold',"Threshold"),('property','use_clamp',"Clamp"),('property','clamp',"Maximum")],"Glare": [('property','streaks',"Streaks"),('property','angle_offset',"Streaks Angle"),('property','iterations',"Iterations"),('property','fade',"Fade"),('property','color_modulation',"Color Modulation")]},
    'SIMPLE_STAR': {"Highlights": [('socket','Threshold',"Threshold"),('socket','Smoothness',"Smoothness"),('socket','Clamp',"Clamp"),('socket','Maximum',"Maximum")],"Adjust": [('socket','Strength',"Strength"),('socket','Saturation',"Saturation"),('socket','Tint',"Tint")],"Glare": [('property','iterations',"Iterations"),('property','fade',"Fade"),('socket','Diagonal',"Diagonal")]},
}

def _get_3d_view_space(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D': return space
    return None
def _update_viewport_glow_mode(self, context):
    space_3d = _get_3d_view_space(context)
    if self.enable_viewport_glow and space_3d: space_3d.shading.use_compositor = self.viewport_glow_mode
def _update_viewport_glow_enable(self, context):
    space_3d = _get_3d_view_space(context)
    if space_3d: space_3d.shading.use_compositor = self.viewport_glow_mode if self.enable_viewport_glow else 'DISABLED'

class GlareControlProperties(bpy.types.PropertyGroup):
    target_node_name: bpy.props.StringProperty(name="Target Glare Node Name")
    enable_viewport_glow: bpy.props.BoolProperty(name="Enable Viewport Glow", default=False, update=_update_viewport_glow_enable)
    viewport_glow_mode: bpy.props.EnumProperty(
        name="Mode", items=[('DISABLED',"Disabled",""),('CAMERA',"Camera Only",""),('ALWAYS',"Always","")], default='ALWAYS', update=_update_viewport_glow_mode)
    is_panel_expanded: bpy.props.BoolProperty(name="Glare Controller", default=True)


class SCENE_OT_add_controlled_glare(bpy.types.Operator):
    bl_idname = "scene.add_controlled_glare"; bl_label = "Insert and Control Glare"; bl_options = {'REGISTER','UNDO'}
    def execute(self, context):
        context.scene.use_nodes = True; tree = context.scene.node_tree
        composite_node = self._get_or_create_node(tree, 'CompositorNodeComposite', (800, 400))
        render_layers_node = self._get_or_create_node(tree, 'CompositorNodeRLayers', (0, 400))
        source_socket = self._find_source_socket(composite_node, render_layers_node)
        new_node = tree.nodes.new(type=TARGET_NODE_TYPE); new_node.name = "Controlled_Glare"
        new_node.location = source_socket.node.location + Vector((source_socket.node.width + 100, 0))
        self._link_nodes(tree, source_socket, new_node, composite_node)
        context.scene.glare_tool.target_node_name = new_node.name; self.report({'INFO'}, f"Inserted '{new_node.name}'"); return {'FINISHED'}
    def _get_or_create_node(self, tree, node_type, location=(0,0)):
        node = next((n for n in tree.nodes if n.bl_idname == node_type), None)
        if not node: node = tree.nodes.new(type=node_type); node.location = location
        return node
    def _find_source_socket(self, c, rl):
        return c.inputs.get('Image').links[0].from_socket if c.inputs.get('Image').is_linked else rl.outputs.get('Image')
    def _link_nodes(self, tree, source, middle, end):
        for link in list(end.inputs['Image'].links): tree.links.remove(link)
        tree.links.new(source, middle.inputs['Image']); tree.links.new(middle.outputs['Image'], end.inputs['Image'])
        viewer = tree.nodes.get('Viewer')
        if viewer:
            for link in list(viewer.inputs['Image'].links): tree.links.remove(link)
            tree.links.new(middle.outputs['Image'], viewer.inputs['Image'])
class SCENE_OT_clear_controlled_glare(bpy.types.Operator):
    bl_idname = "scene.clear_controlled_glare"; bl_label = "Clear Controlled Glare Node"
    def execute(self, context): context.scene.glare_tool.target_node_name = ""; return {'FINISHED'}


class GlareControlPanelDrawer:
    def draw_panel_content(self, context):
        props = context.scene.glare_tool
        self._draw_viewport_controls(self.layout, props); self.layout.separator()
        if not context.scene.use_nodes or not context.scene.node_tree:
            self._draw_compositor_disabled(self.layout); return
        tree = context.scene.node_tree; target_node = tree.nodes.get(props.target_node_name)
        if not target_node or target_node.bl_idname != TARGET_NODE_TYPE:
            self._draw_node_selector(self.layout, props, tree, target_node)
        else: self._draw_node_controls(self.layout, target_node)
    def _draw_viewport_controls(self, l, p):
        b=l.box(); b.label(text="Viewport Compositor",icon='RESTRICT_VIEW_ON'); b.prop(p,"enable_viewport_glow");
        if p.enable_viewport_glow:b.prop(p,"viewport_glow_mode",text="")
    def _draw_compositor_disabled(self, l): l.label(text="Compositor is not enabled."); l.operator(SCENE_OT_add_controlled_glare.bl_idname,icon='ADD')
    def _draw_node_selector(self, l, p, t, n):
        if n: l.label(text=f"'{n.name}' is not a Glare node.",icon='ERROR')
        else: l.label(text="No Glare node is being controlled.")
        l.operator(SCENE_OT_add_controlled_glare.bl_idname,icon='ADD'); l.separator(); l.prop_search(p,"target_node_name",t,"nodes",text="Select Node")
    def _draw_node_controls(self, l, n):
        h=l.box(); h.label(text=f"Controlling: {n.name}",icon='NODE_SEL'); b=l.box(); b.prop(n,"glare_type",text="Mode"); b.prop(n,"quality",text="Quality")
        ui_map=PARAMETER_MAP.get(n.glare_type,{});
        for gn,cs in ui_map.items(): self._draw_control_group(b,gn,cs,n)
        l.separator(); l.operator(SCENE_OT_clear_controlled_glare.bl_idname,text="Release Control",icon='X')
    def _draw_control_group(self, l, gn, cs, n):
        b=l.box();
        if gn!="General":b.label(text=gn+":")
        for cd in cs:self._draw_single_control(b,cd,n)
    def _draw_single_control(self, layout, control_def, target_node):
        control_type, api_name, ui_label = control_def
        is_maximum = (control_type=='property' and api_name=='clamp') or (control_type=='socket' and api_name=='Maximum')
        if is_maximum:
            clamp_on = (hasattr(target_node,'use_clamp') and target_node.use_clamp) or ('Clamp' in target_node.inputs and target_node.inputs['Clamp'].default_value)
            if not clamp_on: return
            row = layout.row(); row.alignment = 'RIGHT'; layout = row
        if control_type == 'property': layout.prop(target_node, api_name, text=ui_label)
        elif control_type == 'socket':
            socket = target_node.inputs.get(api_name)
            if socket: layout.prop(socket, "default_value", text=ui_label)


def draw_injected_panel(self, context):
    layout = self.layout
    props = context.scene.glare_tool
    
    box = layout.box()
    box.prop(props, "is_panel_expanded", icon='IMAGE_RGB_ALPHA', emboss=True, text="Glare Controller")
    
    if props.is_panel_expanded:
        drawer = GlareControlPanelDrawer()
        drawer.layout = box
        drawer.draw_panel_content(context)

def register_panel():
    try:
        bpy.types.RENDER_PT_context.prepend(draw_injected_panel)
    except Exception as e:
        print(f"Failed to register Glare Controller panel: {e}")

def unregister_panel():
    try:
        bpy.types.RENDER_PT_context.remove(draw_injected_panel)
    except Exception:
        pass


classes = (
    GlareControlProperties,
    SCENE_OT_add_controlled_glare,
    SCENE_OT_clear_controlled_glare,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.glare_tool = bpy.props.PointerProperty(type=GlareControlProperties)
    register_panel()

def unregister():
    unregister_panel()
    del bpy.types.Scene.glare_tool
    for cls in reversed(classes): bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()