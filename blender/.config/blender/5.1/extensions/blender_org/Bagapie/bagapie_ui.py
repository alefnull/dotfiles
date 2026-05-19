import bpy
import json
from bpy.types import Menu, Panel, UIList, Operator
from bpy.props import StringProperty,BoolProperty,IntProperty
from . presets import bagapieModifiers
import bpy.utils.previews
from .utils import Get_addon_pref, Warning, is_in_local_view
from .bagapie_group_op import check_parent_group, check_group_instance
from .bagapie_ui_op import add_remove_ui, Draw_Scatter_Layer_Content
from bl_keymap_utils.io import keyconfig_merge


class BAGAPIE_MT_pie_menu(Menu):
    bl_label = "BagaPie"
    bl_idname = "BAGAPIE_MT_pie_menu"

    @classmethod
    def poll(cls, context):
        mode = context.mode
        return (mode == 'OBJECT')

    def draw(self, context):
        bagapie_pref = Get_addon_pref()
        layout = self.layout
        target = bpy.context.active_object
        pie = layout.menu_pie()


    #################################################################################
    # PIE UI FOR ARRAY
    #################################################################################
        row = pie.column(align = False)
        col = row.column(align = True)
        col.scale_y = 1.1
        col.scale_x = 0.9
        col.label(text = "Array", icon = "MOD_ARRAY")
        col.operator_enum("wm.array","array_type")
        if bagapie_pref.autoarrayoncurve:
            col.operator("wm.curvearray", text = "Curve Deform")
        row_draw = col.row(align = True)
        row_draw.operator("bagapie.drawarray", text="Draw")
        row_draw.operator("bagapie.asset_browser", text="Asset Browser").import_mode= 'DrawArray'
        
        col.operator('bagapie.array_along_shape')
        col.separator(factor = 3)
        row.separator(factor = 1.5)


    #################################################################################
    # PIE UI FOR ARCHITECTURE
    #################################################################################
        col = pie.column(align = True)
        row = col.row(align = True)
        row.separator(factor = 1)
        col = row.column(align = True)
        col.label(text = "Architecture", icon = "HOME")
        col.scale_y = 1.1
        
        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.wall:
            row.operator('bagapie.wall')
        if bagapie_pref.wallbrick:
            row.operator('bagapie.wallbrick')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.window:
            row.operator("bagapie.window")
        else:
            tips = row.operator("bagapie.tooltips", text="Window", depress = False)
            tips.message = 'Window is now in the new pie menu in Edit Mode ! | D key'
            tips.title = "NEW Window System !"
        if bagapie_pref.pipes:
            row.operator('bagapie.pipes')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.column:
            row.operator('bagapie.column')
        if bagapie_pref.tiles:
            row.operator('bagapie.tiles')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.beamwire:
            row.operator('bagapie.beamwire')
        if bagapie_pref.beam:
            row.operator('bagapie.beam')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.linearstair:
            row.operator('bagapie.linearstair')
        if bagapie_pref.stairspiral:
            row.operator('bagapie.spiralstair')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.floor:
            row.operator('bagapie.floor')
        if bagapie_pref.handrail:
            row.operator('bagapie.handrail')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.cable:
            row.operator('bagapie.cable')
        if bagapie_pref.fence:
            row.operator('bagapie.fence')
        if bagapie_pref.siding:
            row.operator('bagapie.siding')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.cable:
            row.operator('bagapie.paving')
        if bagapie_pref.fence:
            row.operator('bagapie.grid')

        row = col.row(align = True)
        row = row.split(factor=0.5, align=True)
        if bagapie_pref.siding:
            row.operator('bagapie.perforated_grid')
        if bagapie_pref.siding:
            row.operator('bagapie.plank')

        col.separator(factor = 8)


    #################################################################################
    # PIE UI FOR BOOLEAN
    #################################################################################
        col = pie.column()
        col.label(text = "Boolean", icon = "MOD_BOOLEAN")
        split = col.split(align = True)
        split.scale_y = 1.2
        split.scale_x = 2.2
        split.operator_enum("wm.boolean", "operation_type")


    #################################################################################
    # PIE UI FOR SCATTER
    #################################################################################
        col = pie.column(align = True)
        col.scale_y = 1.2
        col.scale_x = 0.9
        col.label(text = "Scattering", icon = "OUTLINER_OB_CURVES")
        if bagapie_pref.scatter:
            row = col.row(align=True)
            split = row.split(factor=0.45, align=True)
            split.operator("wm.scatter").paint_mode = False
            split.operator("bagapie.asset_browser", text="Asset Browser").import_mode= 'Scatter'
        if bagapie_pref.scatterpaint:
            row = col.row(align=True)
            split = row.split(factor=0.45, align=True)
            split.operator("wm.scatter",text = "Scatter Paint").paint_mode = True
            split.operator("bagapie.asset_browser", text="Asset Browser").import_mode= 'ScatterPaint'
        if bagapie_pref.pointsnapinstance:
            row = col.row(align=True)
            split = row.split(factor=0.45, align=True)
            split.operator("bagapie.pointsnapinstance",text = "Snap Asset")
            split.operator("bagapie.asset_browser", text="Asset Browser").import_mode= 'PointSnapInstance'
        if bagapie_pref.ivy:
            col.operator("bagapie.ivy")


    #################################################################################
    # PIE UI FOR DEFORM
    #################################################################################
        col = pie.column(align = True)
        col.scale_x = 1.1 # button Width
        row = col.row(align = True)
        col = row.column(align = True)
        col.label(text = "Deformation", icon = "MOD_DISPLACE")
        col.scale_y = 1.2
        if bagapie_pref.displace:
            col.operator("wm.displace")
        if bagapie_pref.instancesdisplace:
            col.operator("bagapie.instancesdisplace")
        if bagapie_pref.deform:
            col.operator('bagapie.deform')
        col.separator(factor = 14)
        row.separator(factor = 4.2)
        col.separator(factor = 10)


    #################################################################################
    # PIE UI FOR EFFECTOR
    #################################################################################
        col = pie.column(align = True)
        row = col.row(align = True)
        row.separator(factor = 5.5)
        col = row.column(align = True)
        col.label(text = "Effector", icon = "PARTICLES")
        col.scale_y = 1.2
        if target is not None:
            if "BagaPie_Scatter" in target.modifiers:
                if bagapie_pref.pointeffector:
                    col.operator("bagapie.pointeffector")
                if bagapie_pref.camculling:
                    col.operator('bagapie.camera')
                col.separator(factor = 27)
            else:
                col.label(text = "No Scatter available")
                col.separator(factor = 30)
        else:
            col.label(text = "No Scatter available")
            col.separator(factor = 30)


    #################################################################################
    # PIE UI FOR MANAGE
    #################################################################################
        col = pie.column(align = True)
        col.scale_x = 1.3 # button Width
        col.separator(factor = 9)
        row = col.row(align = True)
        col = row.column(align = True)

        try:
            prop = target["bagapie"]
        except:
            prop = None

        if prop is not None and bagapie_pref.group:
            col.scale_x = 0.9
            col.separator(factor = 14)
        else:
            col.scale_x = 1.1
            col.separator(factor = 8.5)
        col.label(text = "Manage", icon = "PACKAGE")
        col.scale_y = 1.1

        if bagapie_pref.group:
            col.operator("bagapie.group", text="Create Group")
            col.operator("bagapie.autoinstance", text="To Instance")

        if prop is not None and bagapie_pref.group:
            col.operator("bagapie.ungroup")
            col.operator("bagapie.instance", text = 'Group to Instance')
        if bagapie_pref.proxy:
            col.operator("bagapie.proxy")
        if bagapie_pref.saveasasset:
            col.operator("bagapie.saveasset")
        if bagapie_pref.savematerial:
            col.operator("bagapie.savematerial")
        found_gp_sh = any(
            kmi.idname == "bagapie.group"
            for km, _ in keyconfig_merge(context.window_manager.keyconfigs.user, context.window_manager.keyconfigs.user)
            for kmi in km.keymap_items
        )
        if found_gp_sh==False:
            col.operator('bagapie.replace_shortcut', text="Add Group Key")

        row.separator(factor = 3.5) # X Offset Right


    #################################################################################
    # PIE UI FOR TUTORIALS
    #################################################################################
        col = pie.column(align = True)
        col.separator(factor = 7)
        row = col.row(align = True)
        row.separator(factor = 5)
        col = row.column(align = True)
        col.separator(factor = 12)
        col.label(text = "About", icon = "URL")
        col.scale_y = 1.2
        col.operator("wm.url_open", text="Tutorials", icon = 'PLAY').url = "https://youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu&si=Y4MRQn_aTIQUXOpw"
        col.operator("wm.url_open", text="Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"
        if not bagapie_pref.hide_geopack:
            col.operator("bagapie.geopack_create_modifier")


class BAGAPIE_UL_List(UIList):
    """BagaPie UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        val = json.loads(item.val)
        name = val['name']
        if name.startswith('BP_A'):
            label = name.removeprefix('BP_Assets_')
            icon = 'MATERIAL'
        else :
            label = bagapieModifiers[name]['label']
            icon = bagapieModifiers[name]['icon']

        obj = context.object
        modifiers = val['modifiers']

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            mo_type = val['name']

            if mo_type == 'scatter':
                layout.label(text=modifiers[3], icon = icon)
            else:
                layout.label(text=label, icon = icon)
            row = layout.row(align=True)

            # List of modifier type to avoid or apply/remove
            assets_type_list = ["stump","tree","grass","rock","plant"]
            avoid_list = ["pointeffector","pointsnapinstance","instancesdisplace","camera"]
            for a in assets_type_list:
                avoid_list.append(a)

            # icon set
            if mo_type == "scatter":
                nodes = obj.modifiers[modifiers[0]].node_group.nodes
                scatt_node = nodes[modifiers[1]]
                scatt_nde_visibility_op = scatt_node.inputs[22].default_value
                scatt_nde_visibility_bool = scatt_node.inputs[23].default_value

                if nodes.get('BagaPie_Camera_Culling'):
                    cam_cull_node = nodes.get('BagaPie_Camera_Culling')
                    if len(scatt_node.inputs[24].links)>0 and scatt_node.inputs[24].links[0].from_node == cam_cull_node:
                        props = row.operator('use.cameracullingonlayer', text='', depress = True, icon = 'OUTLINER_OB_CAMERA')
                        props.index = index
                        props.from_list = True
                    else:
                        props = row.operator('use.cameracullingonlayer', text='', depress = False, icon = 'CAMERA_DATA')
                        props.index = index
                        props.from_list = True

                if not scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif not scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "pointeffector":
                
                scatt_nde_visibility_op = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[5].default_value
                scatt_nde_visibility_bool = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[6].default_value

                if not scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif not scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "camera":
                
                scatt_nde_visibility_op = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[3].default_value
                scatt_nde_visibility_bool = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]].inputs[4].default_value

                if not scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_OFF'

                elif scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    render_icon = 'RESTRICT_RENDER_ON'

                elif not scatt_nde_visibility_op and not scatt_nde_visibility_bool:
                    viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type == "wallbrick":
                if obj.type == 'MESH':
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    if not obj.modifiers[modifiers[0]].show_viewport:
                        viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'
                    if not obj.modifiers[modifiers[0]].show_render:
                        render_icon = 'RESTRICT_RENDER_ON'
                else:
                    viewport_icon = 'RESTRICT_VIEW_OFF'
                    if not obj.modifiers[modifiers[1]].show_viewport:
                        viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'
                    if not obj.modifiers[modifiers[1]].show_render:
                        render_icon = 'RESTRICT_RENDER_ON'

            elif mo_type not in assets_type_list and not mo_type.startswith('BP_A'):
                viewport_icon = 'RESTRICT_VIEW_OFF'
                if modifiers[0] in obj.modifiers:
                    if not obj.modifiers[modifiers[0]].show_viewport:
                        viewport_icon = 'RESTRICT_VIEW_ON'
                    render_icon = 'RESTRICT_RENDER_OFF'
                    if not obj.modifiers[modifiers[0]].show_render:
                        render_icon = 'RESTRICT_RENDER_ON'

            # APPLY
            if mo_type not in avoid_list and not mo_type.startswith('BP_A'):
                row.operator("apply.modifier",text="", icon='CHECKMARK')
            # REMOVE
            if mo_type not in assets_type_list and not mo_type.startswith('BP_A'):
                row.operator('bagapie.'+ name +'_remove', text="", icon='REMOVE').index=index
            # VISIBILITY
            if mo_type not in assets_type_list and not mo_type.startswith('BP_A'):
                if modifiers[0] in obj.modifiers:
                    row.operator("hide.viewport",text="", icon=viewport_icon).index=index
                    row.operator("hide.render",text="", icon=render_icon).index=index


class BAGAPIE_PT_modifier_panel(Panel):
    bl_idname = 'BAGAPIE_PT_modifier_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BagaPie"
    bl_label = "BagaPie Modifier"

    use_random: bpy.props.BoolProperty(default=False) # type: ignore

    @classmethod
    def poll(cls, context):
        o = context.object
        return (
            o is not None and
            o.type == 'MESH' or 'CURVE'
        )

    def draw(self, context):
        layout = self.layout
        obj = context.object
        obj_allowed_types = ["MESH","CURVE","EMPTY"]
        displaydoc = True
        bagapie_pref = Get_addon_pref()

        if obj and obj.type in obj_allowed_types:
            col = layout.column()
            if obj.bagapieIndex < len(obj.bagapieList):

                displaydoc = False
                
                col.template_list("BAGAPIE_UL_List", "The_List", obj,
                                "bagapieList", obj, "bagapieIndex")

                val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                mo_type = val['name']
                modifiers = val['modifiers']

                if mo_type.startswith('BP_A'): # OLD STUFF, MUST BE REMOVED IN THE FUTURE
                    label = mo_type.removeprefix('BP_Assets_')
                    icon = 'MATERIAL'
                else :
                    label = bagapieModifiers[mo_type]['label']
                    icon = bagapieModifiers[mo_type]['icon']

                if mo_type == "wall":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text=label, icon=icon)

                    box.prop(obj.modifiers[modifiers[1]], 'screw_offset', text="Wall Height")
                    box.prop(obj.modifiers[modifiers[2]], 'thickness', text="Wall Thickness")
                    box.prop(obj.modifiers[modifiers[2]], 'offset', text="Wall Axis Offset")

                elif mo_type == "wallbrick":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text=label, icon=icon)

                    if obj.type == 'MESH':
                        modifier = obj.modifiers[modifiers[0]]
                    else:
                        modifier = obj.modifiers[modifiers[1]]
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_2"]', text="Height")
                    box.prop(modifier, '["Input_3"]', text="Thickness")
                    box.prop(modifier, '["Input_4"]', text="Length")
                    box.label(text="Material :")
                    box.prop_search(modifier, '["Input_17"]', bpy.data, "materials", text="", icon="MATERIAL")

                    box = layout.box()
                    box = box.column(align=False)
                    box.prop(modifier, '["Input_5"]', text="Row Count")
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_6"]', text="Row Offset")
                    box.prop(modifier, '["Input_7"]', text="Horizontal Offset")
                    box.prop(modifier, '["Input_8"]', text="Flip")

                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.label(text="Position Min / Max")
                    row = box.row()
                    row.prop(modifier, '["Input_9"]', text="")
                    row = box.row()
                    row.prop(modifier, '["Input_10"]', text="")
                    box.label(text="Rotation Min / Max")
                    row = box.row()
                    row.prop(modifier, '["Input_11"]', text="")
                    row = box.row()
                    row.prop(modifier, '["Input_12"]', text="")
                    box.label(text="Scale Min / Max")
                    row = box.row()
                    row.prop(modifier, '["Input_13"]', text="")
                    row = box.row()
                    row.prop(modifier, '["Input_14"]', text="")
                    
                    box = layout.box()
                    row = box.row()
                    row.label(text="Deformation")
                    box = box.column(align=True)
                    row = box.row()
                    row.prop(modifier, '["Input_15"]', text="")
                    row = box.row()
                    row.prop(modifier, '["Input_16"]', text="Scale")

                elif mo_type == "pipes":
                    modifier_header_basic(col)
                    box = layout.box()
                    add_remove_ui(col, "Input_13")
                    box.label(text="Pipe", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    row = box.row(align=True)
                    input_index = "Input_29"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    box.prop(modifier, '["Input_2"]', text="Radius")
                    box.prop(modifier, '["Input_10"]', text="Profile Resolution")
                    box.prop(modifier, '["Input_3"]', text="Offset")
                    box.prop(modifier, '["Input_4"]', text="Precision")
                    box.prop(modifier, '["Input_5"]', text="Resolution")
                    box.prop(modifier, '["Input_24"]', text="Bevel")
                    box.prop(modifier, '["Input_28"]', text="End Bevel")
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Junctions")
                    box.prop(modifier, '["Input_6"]', text="Density")
                    box.prop(modifier, '["Input_7"]', text="Depth")
                    box.label(text="Support")
                    box.prop(modifier, '["Input_8"]', text="Probability")
                    box.prop(modifier, '["Input_9"]', text="Radius")
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Random")
                    
                    inputs = [
                        ("Input_14", "Use Valve"),
                        ("Input_15", "Use Jonctions"),
                        ("Input_20", "Use Support"),
                        ("Input_22", "Use Pipe End"),
                    ]
                    for input_index, text in inputs:
                        props = box.operator('switch.button', text=text, depress=(modifier[input_index] != gn_bool_version(1)))
                        props.index = input_index
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Custom :",  icon = "MESH_DATA")
                    
                    inputs = [
                        ("Input_26", "Use Custom Valve", "Input_25"),
                        ("Input_16", "Use Custom Jonctions", "Input_17"),
                        ("Input_11", "Support Custom Profile", "Input_12")
                    ]
                    for input_index, text, prop_index in inputs:
                        depress = (modifier[input_index] == gn_bool_version(1))
                        props = box.operator('switch.button', text=text, depress=depress)
                        props.index = input_index
                        if depress:
                            box.prop_search(modifier, f'["{prop_index}"]', bpy.data, "objects", text="", icon="OBJECT_DATA")

                    # TARGET
                    box.separator(factor = 3)
                    box.label(text="Target :", icon = "MOD_SHRINKWRAP")
                    box.prop_search(modifier, '["Input_13"]', bpy.data, "collections", text="", icon="OUTLINER_COLLECTION")

                    # MATERIAL
                    box.separator(factor = 3)
                    box.label(text="Materials", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_18"]', bpy.data, "materials", text="Jonction", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_19"]', bpy.data, "materials", text="Valve", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_21"]', bpy.data, "materials", text="Support", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_23"]', bpy.data, "materials", text="Pipe", icon="MATERIAL")

                    box.separator(factor = 3)
                    box.label(text="Tips", icon = "INFO")
                    box.label(text="This modifier break UVs.")
                    box.label(text="You can still get UVs as an attribute")
                    box.label(text="Once the modifier is applied :")
                    box.label(text="Prop > Obj Data Prop > Attributes")

                elif mo_type == "beamwire":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Beam Wire", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_2"]', text="Sides Count")
                    box.prop(modifier, '["Input_3"]', text="Radius")
                    box.prop(modifier, '["Input_4"]', text="Section Height")
                    box.prop(modifier, '["Input_5"]', text="Levels")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Diameter")
                    box.prop(modifier, '["Input_8"]', text="Diagonal")
                    box.prop(modifier, '["Input_7"]', text="Beam")
                    
                    box.label(text="Profile")
                    input_index = "Input_6"
                    props = box.operator('switch.button', text='Triangulate', depress=(modifier[input_index] == gn_bool_version(1)), icon="MOD_TRIANGULATE")
                    props.index = input_index

                    row = box.row(align=True)
                    row.label(text="Beam")
                    inputs = [
                        ("Input_11", "MESH_CIRCLE", True),
                        ("Input_11", "MESH_PLANE", False)
                    ]
                    for input_index, icon, depress_state in inputs:
                        props = row.operator('switch.button', text='', depress=(modifier[input_index] == gn_bool_version(1)) == depress_state, icon=icon)
                        props.index = input_index

                    row = box.row(align=True)
                    row.label(text="Bracing")
                    inputs = [
                        ("Input_9", "MESH_CIRCLE", True),
                        ("Input_9", "MESH_PLANE", False)
                    ]
                    for input_index, icon, depress_state in inputs:
                        depress = (modifier[input_index] == gn_bool_version(1)) if depress_state else (modifier[input_index] != gn_bool_version(1))
                        props = row.operator('switch.button', text='', depress=depress, icon=icon)
                        props.index = input_index

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_13"]', bpy.data, "materials", text="", icon="MATERIAL")

                elif mo_type == "linearstair":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_3"]', text="Depth")
                    box.prop(modifier, '["Input_4"]', text="Step Height")
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_6"]', text="Width")
                    box.prop(modifier, '["Input_8"]', text="Thickness")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Properties")

                    row = box.row(align=True)
                    row.label(text="Type")

                    input_index = "Input_15"
                    props = row.operator('switch.button', text='', depress = modifier[input_index] == gn_bool_version(1), icon = "MESH_PLANE")
                    props.index = input_index
                    props = row.operator('switch.button', text='', depress = not modifier[input_index] == gn_bool_version(1), icon = "SNAP_FACE")
                    props.index = input_index


                    row = box.row(align=True)
                    row.label(text="Use Handrail")
                    input_index = "Input_18"
                    props = row.operator('switch.button', text='', depress = modifier[input_index] == gn_bool_version(1), icon = "X")
                    props.index = input_index
                    props = row.operator('switch.button', text='', depress = not modifier[input_index] == gn_bool_version(1), icon = "CHECKMARK")
                    props.index = input_index
                    
                    row = box.row(align=True)
                    row.label(text="Use Glass")
                    input_index = "Input_23"
                    props = row.operator('switch.button', text='', depress = modifier[input_index] == gn_bool_version(1), icon = "X")
                    props.index = input_index
                    props = row.operator('switch.button', text='', depress = not modifier[input_index] == gn_bool_version(1), icon = "CHECKMARK")
                    props.index = input_index

                    input_index = "Input_15"
                    if modifier[input_index] == gn_bool_version(1):
                        box = layout.box()
                        box.label(text="Stringers")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_16"]', text="Width")
                        box.prop(modifier, '["Input_17"]', text="Height")
                        box.prop(modifier, '["Input_19"]', text="Offset X")
                        box.prop(modifier, '["Input_20"]', text="Offset Y")

                    input_index = "Input_18"
                    if modifier[input_index] == gn_bool_version(0):
                        box = layout.box()
                        box.label(text="Handrail")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_9"]', text="Offset")
                        box.prop(modifier, '["Input_10"]', text="Height")
                        box.prop(modifier, '["Input_11"]', text="Radius")
                        box.prop(modifier, '["Input_12"]', text="Balusters Radius")
                        box.prop(modifier, '["Input_13"]', text="Balusters Distance")
                        box.prop(modifier, '["Input_14"]', text="Handrail Resolution")
                        input_index = "Input_23"
                        if modifier[input_index] == gn_bool_version(0):
                            box.prop(modifier, '["Input_21"]', text="Glass Size")
                            box.prop(modifier, '["Input_22"]', text="Glass Offset")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_24"]', bpy.data, "materials", text="Glass", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_25"]', bpy.data, "materials", text="Baluster", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_26"]', bpy.data, "materials", text="Handrail", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_27"]', bpy.data, "materials", text="Stringer", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_28"]', bpy.data, "materials", text="Step", icon="MATERIAL")

                elif mo_type == "tiles":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Tile", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    col = box.column(align=True)
                    row = col.row(align=True)
                    input_index = "Input_11"
                    props = row.operator('switch.button', text='Procedural', depress = modifier[input_index] == gn_bool_version(0))
                    props.index = input_index
                    props = row.operator('switch.button', text='Custom', depress = not modifier[input_index] == gn_bool_version(0))
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(0):

                        col.prop(modifier, '["Input_6"]', text="Type")
                        col.prop(modifier, '["Input_2"]', text="Resolution")

                        col = box.column(align=True)
                        col.prop(modifier, '["Input_5"]', text="Length")
                        col.prop(modifier, '["Input_20"]', text="Height")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        col.prop(modifier, '["Input_4"]', text="Width Offset")
                        col.prop(modifier, '["Input_18"]', text="Thickness")

                        col = box.column(align=True)
                        col.prop(modifier, '["Input_7"]', text="Angle Tile")
                    else:
                        box.prop_search(modifier, '["Input_12"]', bpy.data, "objects", text="", icon="OBJECT_DATA")
                    
                    # REPARTITION
                    box = layout.box()
                    box.label(text="Repartition", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_8"]', text="Count X")
                    col.prop(modifier, '["Input_9"]', text="Count Y")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_23"]', text="Biais")
                    col.prop(modifier, '["Input_19"]', text="Superposition X")
                    col.prop(modifier, '["Input_10"]', text="Superposition Y")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_13"]', text="Triangulate")
                    col.prop(modifier, '["Input_14"]', text="Shift X")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_15"]', text="Angle")

                    box = layout.box()
                    box.label(text="Random", icon=icon)
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_16"]', text="Scale")
                    col.prop(modifier, '["Input_17"]', text="Rotation")
                    col.prop(modifier, '["Input_21"]', text="Seed")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_22"]', bpy.data, "materials", text="", icon="MATERIAL")

                elif mo_type == "beam":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_2"]', text="Width")
                    box.prop(modifier, '["Input_3"]', text="Height")
                    box.prop(modifier, '["Input_8"]', text="Length")
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_4"]', text="Thickness")
                    box.prop(modifier, '["Input_5"]', text="Int Offset")
                    box.prop(modifier, '["Input_6"]', text="Bevel")
                    box = box.column(align=True)
                    box.prop(modifier, '["Input_7"]', text="Bevel Count")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_9"]', bpy.data, "materials", text="", icon="MATERIAL")

                elif mo_type == "column":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_6"]', text="Height")
                    input_index = "Input_7"
                    row = box.row(align=True)
                    row.label(text="Profile")
                    if modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='', depress = True, icon = 'MESH_PLANE')
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = 'MESH_PLANE')
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='', depress = True, icon = 'MESH_CIRCLE')
                    else:
                        props = row.operator('switch.button', text='', depress = False, icon = 'MESH_CIRCLE')
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(0):
                        box.prop(modifier, '["Input_4"]', text="Width")
                        box.prop(modifier, '["Input_5"]', text="Depth")
                        box.separator(factor = 1)
                        box.label(text="Bevel")
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_2"]', text="Size")
                        box.prop(modifier, '["Input_3"]', text="Count")
                    else:
                        box.prop(modifier, '["Input_9"]', text="Radius")
                        box.prop(modifier, '["Input_8"]', text="Resolution")

                    
                    box.label(text="Material")
                    box.prop_search(modifier, '["Input_11"]', bpy.data, "materials", text="", icon="MATERIAL")

                elif mo_type == "deform":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)

                    box.label(text="Blend")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_2"]', text="X")
                    row.prop(modifier, '["Input_3"]', text="Y")
                    row.prop(modifier, '["Input_4"]', text="Z")
                    row = box.row(align=True)
                    input_index = "Input_8"
                    if modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='Flip', depress = True)
                    else:
                        props = row.operator('switch.button', text='Flip', depress = False)
                    props.index = input_index
                    box.separator(factor = 1)
                    box.label(text="Twist")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_5"]', text="X")
                    row.prop(modifier, '["Input_6"]', text="Y")
                    row.prop(modifier, '["Input_7"]', text="Z")

                elif mo_type == "floor":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    row = box.row(align=True)
                    row.label(text="X")
                    row.label(text="Y")
                    row.label(text="Z")
                    row = box.row(align=True)
                    row.prop(modifier, '["Input_3"]', text="")
                    row.prop(modifier, '["Input_4"]', text="")
                    row.prop(modifier, '["Input_5"]', text="")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_6"]', text="Vertices X")
                    box.prop(modifier, '["Input_7"]', text="Vertices Y")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_8"]', text="Offset X")
                    box.prop(modifier, '["Input_10"]', text="Offset Y")
                    box.separator(factor = 1)
                    box.prop(modifier, '["Input_11"]', text="Random")
                    box.prop(modifier, '["Input_12"]', text="Offset")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_15"]', bpy.data, "materials", text="", icon="MATERIAL")

                    # Custom mesh
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Custom", icon = "MESH_DATA")
                    input_index = "Input_14"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Use Custom Mesh', depress = True)
                        box.prop_search(modifier, '["Input_13"]', bpy.data, "objects", text="", icon="OBJECT_DATA")
                    else:
                        props = box.operator('switch.button', text='Use Custom Mesh', depress = False)
                    props.index = input_index

                elif mo_type == "spiralstair":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_3"]', text="Radius")
                    box.prop(modifier, '["Input_2"]', text="Width")
                    box.prop(modifier, '["Input_7"]', text="Step Height")
                    box.prop(modifier, '["Input_6"]', text="Rotation")
                    box.prop(modifier, '["Input_8"]', text="Step Thickness")
                    input_index = "Input_9"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Invert', depress = True)
                    else:
                        props = box.operator('switch.button', text='Invert', depress = False)
                    props.index = input_index

                    # HANDRAIL
                    box = layout.box()
                    box.label(text="Handrail")
                    box = box.column()
                    row = box.row(align=True)
                    input_index = "Input_18"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Left', depress = False)
                    else:
                        props = row.operator('switch.button', text='Left', depress = True)
                    props.index = input_index
                    input_index = "Input_17"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Right', depress = False)
                    else:
                        props = row.operator('switch.button', text='Right', depress = True)
                    props.index = input_index
                    box = box.column(align=True)
                    if modifier["Input_17"] == gn_bool_version(0) or modifier["Input_18"] == gn_bool_version(0):
                        box.prop(modifier, '["Input_11"]', text="Height")
                        box.prop(modifier, '["Input_10"]', text="Offset")
                        box.prop(modifier, '["Input_14"]', text="Baluster Distance")
                        box.prop(modifier, '["Input_13"]', text="Resolution")
                        box = box.column()
                        box = box.column(align=True)
                        box.prop(modifier, '["Input_12"]', text="Radius")
                        box.prop(modifier, '["Input_38"]', text="Profile Resolution")
                    
                    box.separator(factor = 1)
                    # GLASS
                    input_index = "Input_15"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Use Glass', depress = True)
                    else:
                        props = box.operator('switch.button', text='Use Glass', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        box.prop(modifier, '["Input_35"]', text="Glass Height")
                        box.prop(modifier, '["Input_40"]', text="Glass Width")

                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Support")
                    input_index = "Input_25"
                    if modifier[input_index] == gn_bool_version(0):
                        props = box.operator('switch.button', text='Column', depress = False)
                    else:
                        props = box.operator('switch.button', text='Column', depress = True)
                    props.index = input_index
                    if modifier["Input_25"] == gn_bool_version(1):
                        box.prop(modifier, '["Input_39"]', text="Resolution")

                    box.label(text="Stringer")
                    row = box.row(align=True)
                    input_index = "Input_21"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Left', depress = False)
                    else:
                        props = row.operator('switch.button', text='Left', depress = True)
                    props.index = input_index
                    input_index = "Input_22"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Right', depress = False)
                    else:
                        props = row.operator('switch.button', text='Right', depress = True)
                    props.index = input_index

                    box = box.column()
                    if modifier["Input_21"] == gn_bool_version(0) or modifier["Input_22"] == gn_bool_version(0):
                        box.label(text="Width")
                        row = box.row(align=True)
                        if modifier["Input_21"] == gn_bool_version(0):
                            row.prop(modifier, '["Input_19"]', text="L")
                        if modifier["Input_22"] == gn_bool_version(0):
                            row.prop(modifier, '["Input_20"]', text="R")
                        box.label(text="Offset")
                        row = box.row(align=True)
                        if modifier["Input_21"] == gn_bool_version(0):
                            row.prop(modifier, '["Input_33"]', text="L")
                        if modifier["Input_22"] == gn_bool_version(0):
                            row.prop(modifier, '["Input_34"]', text="R")
                        box.prop(modifier, '["Input_23"]', text="Thickness")
                        box.prop(modifier, '["Input_24"]', text="Offset Z")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_27"]', bpy.data, "materials", text="Baluster", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_28"]', bpy.data, "materials", text="Glass", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_29"]', bpy.data, "materials", text="Column", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_30"]', bpy.data, "materials", text="Handrail", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_31"]', bpy.data, "materials", text="Step", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_32"]', bpy.data, "materials", text="Stringer", icon="MATERIAL")

                elif mo_type == "handrail":
                    modifier_header_basic(col)

                    # MAIN
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_8"]', text="Height")
                    box.prop(modifier, '["Input_2"]', text="Module Length")
                    row = box.row(align=True)
                    input_index = "Input_32"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index


                    # GLASS

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_15"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Glass', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='Glass', depress = False)
                    props.index = input_index

                    box = box.column(align=True)
                    if modifier[input_index] == gn_bool_version(1):
                        box.prop(modifier, '["Input_4"]', text="Size")
                        box.prop(modifier, '["Input_9"]', text="Offset")
                        box.prop(modifier, '["Input_10"]', text="Thickness")
                        box.prop(modifier, '["Input_3"]', text="Proportion")
                        box.separator(factor = 1)
                            
                        input_index = "Input_14"
                        row = box.row()
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Use Connector', depress = True)
                        else:
                            row.scale_y = 1.5
                            props = row.operator('switch.button', text='Use Connector', depress = False)
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == gn_bool_version(1):
                            box.prop(modifier, '["Input_5"]', text="Offset")
                            box.prop(modifier, '["Input_47"]', text="Length")
                            row = box.row(align=True)
                            row.prop(modifier, '["Input_6"]', text="X")
                            row.prop(modifier, '["Input_7"]', text="Y")


                    # BALUSTER

                    box = layout.box()
                    input_index = "Input_17"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Baluster', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Baluster', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_16"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        input_index = "Input_16"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == gn_bool_version(1):
                            box.prop(modifier, '["Input_20"]', text="Width")
                            box.prop(modifier, '["Input_21"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_18"]', text="Radius")
                            box.prop(modifier, '["Input_19"]', text="Resolution")


                    # HANDRAIL

                    box = layout.box()
                    input_index = "Input_22"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Handrail', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Handrail', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_23"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == gn_bool_version(1):
                            box.prop(modifier, '["Input_26"]', text="Width")
                            box.prop(modifier, '["Input_27"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_24"]', text="Radius")
                            box.prop(modifier, '["Input_25"]', text="Resolution")
                        box.prop(modifier, '["Input_28"]', text="Curve Resolution")


                    # HORIZONTAL BALUSTER

                    box = layout.box()
                    input_index = "Input_33"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Horizontal Baluster', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Horizontal Baluster', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        box = box.column(align=True)
                            
                        row = box.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_36"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        box = box.column(align=True)
                        if modifier[input_index] == gn_bool_version(1):
                            box.prop(modifier, '["Input_39"]', text="Width")
                            box.prop(modifier, '["Input_40"]', text="Height")
                        else:
                            box.prop(modifier, '["Input_38"]', text="Radius")
                            box.prop(modifier, '["Input_37"]', text="Resolution")
                        box.prop(modifier, '["Input_35"]', text="Curve Resolution")
                        box.prop(modifier, '["Input_41"]', text="Offset Z")
                        box.prop(modifier, '["Input_42"]', text="Distance")
                        box.prop(modifier, '["Input_43"]', text="Count")
                        box.prop(modifier, '["Input_45"]', text="Offset")


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_31"]', bpy.data, "materials", text="Glass", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_46"]', bpy.data, "materials", text="Glass Connector", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_29"]', bpy.data, "materials", text="Baluster", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_30"]', bpy.data, "materials", text="Handrail", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_44"]', bpy.data, "materials", text="Baluster", icon="MATERIAL")

                elif mo_type == "door":
                    modifier_header_basic(col)

                    modifier = obj.modifiers[modifiers[0]]

                    # MAIN
                    box = layout.box()
                    box.label(text="Main")
                    box = box.column(align=True)
                    box.prop(modifier, '["Socket_46"]', text="Global Offset")
                    box.prop(modifier, '["Socket_27"]', text="Depth")
                    box.prop(modifier, '["Socket_63"]', text="Door Offset")

                    child_door_bool = None
                    for child in obj.children:
                        if child.name.startswith("BagaPie_Door_Bool") and child.data == obj.data:
                            child_door_bool=child
                            break
                        elif child.data == obj.data:
                            child_door_bool=child
                            break
                        elif child.name.startswith("BagaPie_Door_Bool"):
                            child_door_bool=child
                            break
                    
                    if child_door_bool:
                        solidify_modifier = next((mod for mod in child_door_bool.modifiers if mod.type == 'SOLIDIFY'), None)
                        if solidify_modifier:
                            box.prop(solidify_modifier, "thickness", text="Boolean Thickness")

                    # DOOR
                    box = layout.box()
                    box.label(text="Door")

                    # Regroupement des boutons
                    input_index = "Socket_10"
                    props = box.operator('switch.button', text='Double/Simple', depress=not modifier[input_index])
                    props.index = input_index

                    input_index = "Socket_11"
                    props = box.operator('switch.button', text='Flip Side')
                    props.index = input_index

                    input_index = "Socket_76"
                    props = box.operator('switch.button', text='Flip Wall Side', icon="LOOP_BACK")
                    props.index = input_index


                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_47"]', text="Thickness")
                    col.prop(modifier, '["Socket_37"]', text="Random Opening")
                    col.prop(modifier, '["Socket_7"]', text="Opening")

                    col.separator(factor=2)
                    col.label(text="Tweak this if few Shutters fail")
                    col.prop(modifier, '["Socket_12"]', text="Min Height")


                    # DOOR FRAME
                    box = layout.box()
                    input_index = "Socket_23"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Door Frame', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Door Frame', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_69"]', text="A")
                        row.prop(modifier, '["Socket_70"]', text="B")
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_71"]', text="C")
                        row.prop(modifier, '["Socket_72"]', text="D")



                    # WALL FRAME
                    box = layout.box()
                    input_index = "Socket_19"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Wall Frame', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Wall Frame', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_45"]', text="Frame Thickness")



                    # HANDLE
                    box = layout.box()
                    input_index = "Socket_66"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Handle', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Handle', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.label(text="Handle Type")
                        col.prop(modifier, '["Socket_75"]', text="")
                        if modifier["Socket_75"] == 3:
                            box.prop_search(modifier, '["Socket_74"]', bpy.data, "collections", text="Coll", icon="OUTLINER_COLLECTION")
                        elif modifier["Socket_75"] == 0:
                            col.prop(modifier, '["Socket_80"]', text="Position X")
                            col.prop(modifier, '["Socket_77"]', text="Top Offset")
                            col.prop(modifier, '["Socket_78"]', text="Bottom Offset")
                            col.prop(modifier, '["Socket_79"]', text="Radius")
                        elif modifier["Socket_75"] == 1 or 2:
                            col.prop(modifier, '["Socket_80"]', text="Position X")
                            col.prop(modifier, '["Socket_81"]', text="Position Y")
                    

                    # HINGE
                    box = layout.box()
                    input_index = "Socket_14"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Hinge', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Hinge', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_73"]', text="Offset")

                    # MATERIALS
                    box = layout.box()
                    box.label(text="Materials", icon="MATERIAL")
                    col = box.column(align=True)
                    col.prop_search(modifier, '["Socket_65"]', bpy.data, "materials", text="Door", icon="MATERIAL")
                    col.prop_search(modifier, '["Socket_32"]', bpy.data, "materials", text="Frame", icon="MATERIAL")
                    col.prop_search(modifier, '["Socket_36"]', bpy.data, "materials", text="Door Frame", icon="MATERIAL")
                    col.prop_search(modifier, '["Socket_64"]', bpy.data, "materials", text="Handle", icon="MATERIAL")
                    col.prop_search(modifier, '["Socket_35"]', bpy.data, "materials", text="Hinge", icon="MATERIAL")

                elif mo_type == "window_v2":
                    modifier_header_basic(col)
                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Socket_46"]', text="Global Offset")
                    box.prop(modifier, '["Socket_27"]', text="Depth")
                    box.prop(modifier, '["Socket_63"]', text="Windows Offset")

                    child_win_bool = None
                    for child in obj.children:
                        if child.name.startswith("BagaPie_Window_Bool") and child.data == obj.data:
                            child_win_bool=child
                            break
                        elif child.data == obj.data:
                            child_win_bool=child
                            break
                        elif child.name.startswith("BagaPie_Window_Bool"):
                            child_win_bool=child
                            break
                    
                    if child_win_bool:
                        solidify_modifier = next((mod for mod in child_win_bool.modifiers if mod.type == 'SOLIDIFY'), None)
                        if solidify_modifier:
                            box.prop(solidify_modifier, "thickness", text="Boolean Thickness")
                            box.prop(solidify_modifier, "offset", text="Boolean Offset")

                    # REVEAL THICKNESS
                    box = layout.box()
                    input_index = "Socket_19"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Reveal Thickness', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Reveal Thickness', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_45"]', text="Reveal Thickness")

                    # GLASS
                    box = layout.box()
                    input_index = "Socket_21"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Glass', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Glass', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_29"]', text="Offset Glass")

                    # FRAME
                    box = layout.box()
                    input_index = "Socket_22"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Frame', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Frame', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        # Regroupement des propriétés Width et Height
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_2"]', text="Width")
                        row.prop(modifier, '["Socket_3"]', text="Height")
                        col.prop(modifier, '["Socket_24"]', text="Bevel")
                        # Regroupement des propriétés Count Vertical et Count Horizontal
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_4"]', text="Count Vertical")
                        row.prop(modifier, '["Socket_5"]', text="Count Horizontal")

                    # CASING
                    box = layout.box()
                    input_index = "Socket_23"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Casing', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Casing', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        # Regroupement des propriétés Width 1 et Thickness 1
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_17"]', text="Width")
                        row.prop(modifier, '["Socket_18"]', text="Thickness")
                        # Regroupement des propriétés Bevel Radius et Bevel Count
                        row = col.row(align=True)
                        row.prop(modifier, '["Socket_26"]', text="Bevel Radius")
                        row.prop(modifier, '["Socket_38"]', text="Bevel Count")
                        col.prop(modifier, '["Socket_28"]', text="Offset")

                        col.separator(factor=0.5)
                        input_index = "Socket_20"
                        if modifier[input_index]:
                            props = col.operator('switch.button', text='Casing 2', depress=True)
                        else:
                            props = col.operator('switch.button', text='Casing 2', depress=False)
                        props.index = input_index
                        
                        if modifier[input_index]:
                            # Regroupement des propriétés Width 2 et Thickness 2
                            row = col.row(align=True)
                            row.prop(modifier, '["Socket_15"]', text="Width")
                            row.prop(modifier, '["Socket_16"]', text="Thickness")
                            # Regroupement des propriétés Bevel et Bevel Count
                            row = col.row(align=True)
                            row.prop(modifier, '["Socket_25"]', text="Bevel")
                            row.prop(modifier, '["Socket_62"]', text="Bevel Count")
                            col.prop(modifier, '["Socket_61"]', text="Offset")

                    # SHUTTERS
                    box = layout.box()
                    input_index = "Socket_14"
                    if modifier[input_index]:
                        props = box.operator('switch.button', text='Shutters', depress=True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Shutters', depress=False)
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        
                        col.label(text="May fail on some shapes !")
                        col.separator(factor=1)

                        row = col.row(align=True)
                        row.scale_y = 1.5
                        row.operator('switch.button', text='Simple', depress=modifier["Socket_10"]).index = "Socket_10"
                        row.operator('switch.button', text='Double', depress=not modifier["Socket_10"]).index = "Socket_10"
                        
                        if modifier['Socket_10']:
                            props = col.operator('switch.button', text='Flip Side')
                            props.index = "Socket_11"

                        col.separator(factor=0.5)


                        col.prop(modifier, '["Socket_6"]', text="Slide")
                        col.prop(modifier, '["Socket_9"]', text="Length Factor")

                        col.prop(modifier, '["Socket_7"]', text="Opening")
                        col.prop(modifier, '["Socket_37"]', text="Random Opening")



                        col.separator(factor=4)

                        row=col.row(align=True)
                        row.scale_y = 1.5
                        props = row.operator('switch.button', text='Louvered', depress=modifier["Socket_49"])
                        props.index = "Socket_49"
                        props = row.operator('switch.button', text='Solid', depress=not modifier["Socket_49"])
                        props.index = "Socket_49"

                        col.separator(factor=2)

                        if modifier['Socket_49']:
                            col.label(text="Louvers:")
                            row=col.row(align=True)
                            row.scale_y = 1.2
                            props = row.operator('switch.button', text='Count', depress=not modifier["Socket_58"])
                            props.index = "Socket_58"
                            props = row.operator('switch.button', text='Distance', depress=modifier["Socket_58"])
                            props.index = "Socket_58"

                            # Séparation des propriétés Verticales
                            col.label(text="Vertical:")
                            row = col.row(align=True)
                            row.prop(modifier, '["Socket_50"]', text="Thickness")
                            row.prop(modifier, '["Socket_51"]', text="Width")
                            if modifier['Socket_58']:
                                col.prop(modifier, '["Socket_59"]', text="Distance")
                            else:
                                col.prop(modifier, '["Socket_52"]', text="Count")
                            # Séparation des propriétés Horizontales
                            col.label(text="Horizontal:")
                            row = col.row(align=True)
                            row.prop(modifier, '["Socket_54"]', text="Thickness")
                            row.prop(modifier, '["Socket_55"]', text="Width")
                            if modifier['Socket_58']:
                                col.prop(modifier, '["Socket_60"]', text="Distance")
                            else:
                                col.prop(modifier, '["Socket_53"]', text="Count")

                            col.prop(modifier, '["Socket_30"]', text="Angle")

                            col.separator(factor=0.5)

                            props = col.operator('switch.button', text='Frame', depress=modifier["Socket_13"])
                            props.index = "Socket_13"
                            if modifier['Socket_13']:
                                col.prop(modifier, '["Socket_56"]', text="Thickness")
                                col.prop(modifier, '["Socket_57"]', text="Width")

                        else:    
                            col.prop(modifier, '["Socket_47"]', text="Thickness")
                            col.prop(modifier, '["Socket_48"]', text="Scale")

                        col.separator(factor=2)
                        col.label(text="Tweak this if few Shutters fail")
                        col.prop(modifier, '["Socket_12"]', text="Min Height")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon="MATERIAL")
                    box.prop_search(modifier, '["Socket_31"]', bpy.data, "materials", text="Frame", icon="MATERIAL")
                    box.prop_search(modifier, '["Socket_32"]', bpy.data, "materials", text="Casing", icon="MATERIAL")
                    box.prop_search(modifier, '["Socket_33"]', bpy.data, "materials", text="Glass", icon="MATERIAL")
                    box.prop_search(modifier, '["Socket_35"]', bpy.data, "materials", text="Shutters", icon="MATERIAL")
                    box.prop_search(modifier, '["Socket_36"]', bpy.data, "materials", text="Reveal", icon="MATERIAL")

                elif mo_type == "fence":
                    modifier_header_basic(col)

                    # MAIN

                    box = layout.box()
                    box.label(text="Main", icon=icon)

                    modifier = obj.modifiers[modifiers[0]]

                    box = box.column(align=True)
                    box.prop(modifier, '["Input_5"]', text="Height")
                    box.prop(modifier, '["Input_4"]', text="Fence Offset")
                    row = box.row(align=True)
                    input_index = "Input_54"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Curve', depress = False, icon = 'OUTLINER_OB_CURVE')
                    else:
                        props = row.operator('switch.button', text='Curve', depress = True, icon = 'OUTLINER_OB_CURVE')
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='Poly', depress = False, icon = 'OUTLINER_OB_MESH')
                    else:
                        props = row.operator('switch.button', text='Poly', depress = True, icon = 'OUTLINER_OB_MESH')
                    props.index = input_index

                    
                    # BASE WALL

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_35"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Wall', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='Wall', depress = False)
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_2"]', text="Height")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        
                        input_index = "Input_51"
                        if modifier[input_index] == gn_bool_version(1):
                            props = col.operator('switch.button', text='Even Thickness', depress = True)
                        else:
                            props = col.operator('switch.button', text='Even Thickness', depress = False)
                        props.index = input_index
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_44"
                        if modifier[input_index] == gn_bool_version(1):
                            props = col.operator('switch.button', text='Cap Flashing', depress = True)
                        else:
                            props = col.operator('switch.button', text='Cap Flashing', depress = False)
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            col.prop(modifier, '["Input_37"]', text="Height")
                            col.prop(modifier, '["Input_38"]', text="Thickness")
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_53"
                        if modifier[input_index] == gn_bool_version(1):
                            props = col.operator('switch.button', text='Auto Smooth', depress = True)
                        else:
                            props = col.operator('switch.button', text='Auto Smooth', depress = False)
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            col.prop(modifier, '["Input_52"]', text="Angle")
                        



                    # FENCE VERTICAL

                    box = layout.box()
                    box = box.column() #lol
                    row = box.row()
                    input_index = "Input_42"
                    if modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Fence Vertical', depress = True)
                    else:
                        row.scale_y = 2
                        props = row.operator('switch.button', text='Fence Vertical', depress = False)
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_14"]', text="Distance")
                        col.prop(modifier, '["Input_36"]', text="End Wall Offset")
                        col.prop(modifier, '["Input_55"]', text="Offset")
                        col.prop(modifier, '["Input_15"]', text="Scale")
                        col.prop(modifier, '["Input_16"]', text="Scale Random")
                        col.prop(modifier, '["Input_34"]', text="Scale Z Random")
                        
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_6"]', text="Rotation")
                        col.prop(modifier, '["Input_7"]', text="Random Tangent")
                        col.prop(modifier, '["Input_50"]', text="Random Axis")

                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_8"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        if modifier[input_index] == gn_bool_version(1):
                            col.prop(modifier, '["Input_13"]', text="Radius")
                            col.prop(modifier, '["Input_12"]', text="Resolution")
                        else:
                            col.prop(modifier, '["Input_10"]', text="Width")
                            col.prop(modifier, '["Input_11"]', text="Height")
                        



                    # TIMBER POST

                    box = layout.box()
                    input_index = "Input_39"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Timber Post', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Timber Post', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_17"]', text="Spacing")
                        col.prop(modifier, '["Input_18"]', text="Height")
                        col.prop(modifier, '["Input_32"]', text="Offset")
                            
                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.label(text="Profile")
                        input_index = "Input_19"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                        else:
                            props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                        props.index = input_index

                        if modifier[input_index] == gn_bool_version(1):
                            col.prop(modifier, '["Input_23"]', text="Radius")
                            col.prop(modifier, '["Input_22"]', text="Resolution")
                        else:
                            col.prop(modifier, '["Input_20"]', text="Width")
                            col.prop(modifier, '["Input_21"]', text="Height")
                        
                        col.separator(factor=1.5)
                        col = box.column(align=True)
                        input_index = "Input_40"
                        if modifier[input_index] == gn_bool_version(1):
                            props = col.operator('switch.button', text='Fixation', depress = True)
                        else:
                            props = col.operator('switch.button', text='Fixation', depress = False)
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            col.prop(modifier, '["Input_33"]', text="Dimmensions")




                    # HORIZONTAL

                    box = layout.box()
                    input_index = "Input_43"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Horizontal', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Horizontal', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_29"]', text="Base Offset")
                        col.prop(modifier, '["Input_30"]', text="Top Offset")


                        row = col.row(align=True)
                        input_index = "Input_41"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Full', depress = True, icon = 'SNAP_FACE')
                        else:
                            props = row.operator('switch.button', text='Full', depress = False, icon = 'SNAP_FACE')
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Wire', depress = False, icon = 'ALIGN_JUSTIFY')
                        else:
                            props = row.operator('switch.button', text='Wire', depress = True, icon = 'ALIGN_JUSTIFY')
                        props.index = input_index
                        
                        if modifier[input_index] == gn_bool_version(0):
                            col.prop(modifier, '["Input_31"]', text="Count")
                            
                            col = box.column(align=True)
                            row = col.row(align=True)
                            row.label(text="Profile")
                            input_index = "Input_24"
                            if modifier[input_index] == gn_bool_version(1):
                                props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_PLANE')
                            else:
                                props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_PLANE')
                            props.index = input_index
                            if modifier[input_index] == gn_bool_version(1):
                                props = row.operator('switch.button', text=' ', depress = True, icon = 'MESH_CIRCLE')
                            else:
                                props = row.operator('switch.button', text=' ', depress = False, icon = 'MESH_CIRCLE')
                            props.index = input_index

                            if modifier[input_index] == gn_bool_version(1):
                                col.prop(modifier, '["Input_28"]', text="Radius")
                                col.prop(modifier, '["Input_27"]', text="Resolution")
                            else:
                                col.prop(modifier, '["Input_25"]', text="Width")
                                col.prop(modifier, '["Input_26"]', text="Height")


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_45"]', bpy.data, "materials", text="Wall", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_46"]', bpy.data, "materials", text="Cap Flashing", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_47"]', bpy.data, "materials", text="Fence", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_48"]', bpy.data, "materials", text="Main Support", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_49"]', bpy.data, "materials", text="Support", icon="MATERIAL")

                    
                    # THANKS
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Thanks !", icon = "FUND")
                    box.label(text="Thanks to Zeroskilz.")
                    box.label(text="He created the Curve to Mesh")
                    box.label(text="Even Thickness node !")

                elif mo_type == "siding":
                    modifier_header_basic(col)

                    box = layout.box()
                    box.label(text="Main", icon='FACESEL')
                    col = box.column(align=True)
                    col.scale_y = 2
                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_19"
                    if modifier[input_index] == gn_bool_version(1):
                        props = col.operator('switch.button', text='Keep Original', depress = True)
                    else:
                        props = col.operator('switch.button', text='Keep Original', depress = False)
                    props.index = input_index

                    
                    # X

                    box = layout.box()
                    box.label(text="X", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_6"
                    if modifier[input_index] == gn_bool_version(1):
                        props = col.operator('switch.button', text='X Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='X Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_10"]', text="Distance")
                        col.prop(modifier, '["Input_11"]', text="Width")
                        col.prop(modifier, '["Input_12"]', text="Thickness")
                        col.prop(modifier, '["Input_16"]', text="Angle")

                    
                    # Y

                    box = layout.box()
                    box.label(text="Y", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_7"
                    if modifier[input_index] == gn_bool_version(1):
                        props = col.operator('switch.button', text='Y Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='Y Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_9"]', text="Distance")
                        col.prop(modifier, '["Input_13"]', text="Width")
                        col.prop(modifier, '["Input_14"]', text="Thickness")
                        col.prop(modifier, '["Input_17"]', text="Angle")

                    
                    # Z

                    box = layout.box()
                    box.label(text="Z", icon=icon)
                    col = box.column(align=True)

                    modifier = obj.modifiers[modifiers[0]]
                    input_index = "Input_8"
                    if modifier[input_index] == gn_bool_version(1):
                        props = col.operator('switch.button', text='Z Axis', depress = True)
                    else:
                        col.scale_y = 2
                        props = col.operator('switch.button', text='Z Axis', depress = False)
                    props.index = input_index

                    if modifier[input_index] == gn_bool_version(1):
                        col = box.column(align=True)
                        col.prop(modifier, '["Input_4"]', text="Distance")
                        col.prop(modifier, '["Input_3"]', text="Width")
                        col.prop(modifier, '["Input_2"]', text="Thickness")
                        col.prop(modifier, '["Input_15"]', text="Angle")

                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_18"]', bpy.data, "materials", text="", icon="MATERIAL")

                elif mo_type == "cable":
                    modifier_header_basic(col)
                    modifier = obj.modifiers[modifiers[0]]

                    add_remove_ui(col, "Input_28")

                    # SHAPE
                    box = layout.box()
                    box.label(text="Shape", icon=icon)

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_2"]', text="Gravity")
                    col.prop(modifier, '["Input_29"]', text="Rigidity")
                    col.prop(modifier, '["Input_8"]', text="Resolution")
                    col.prop(modifier, '["Input_7"]', text="Smooth")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_4"]', text="Start Offset")
                    col.prop(modifier, '["Input_5"]', text="Start Rigidity")
                    col.prop(modifier, '["Input_9"]', text="Edge Collision")

                    # PROFIL
                    box = layout.box()
                    box.label(text="Profil", icon="PROP_OFF")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_11"]', text="Radius")
                    col.prop(modifier, '["Input_12"]', text="Cable Count")
                    col.prop(modifier, '["Input_6"]', text="Cable Radius")
                    col.prop(modifier, '["Input_13"]', text="Rotation")
                    col.prop(modifier, '["Input_10"]', text="Resolution")

                    # RANDOM
                    box = layout.box()
                    box.label(text="Randomize")

                    col = box.column(align=True)
                    col.prop(modifier, '["Input_14"]', text="Radius Noise")
                    col.prop(modifier, '["Input_18"]', text="Radius Noise Scale")
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_15"]', text="Radius per Curve")
                    col.prop(modifier, '["Input_16"]', text="Radius offset")
                    col = box.column(align=True)
                    col.prop(modifier, '["Input_17"]', text="Tilt Noise")
                    col.prop(modifier, '["Input_19"]', text="Tilt Noise Scale")

                    # FIXATION
                    box = layout.box()
                    input_index = "Input_34"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Fixation', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Fixation', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                        row = box.row(align=True)
                        input_index = "Input_23"
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Procedural', depress = False)
                        else:
                            props = row.operator('switch.button', text='Procedural', depress = True)
                        props.index = input_index
                        if modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Custom', depress = True)
                        else:
                            props = row.operator('switch.button', text='Custom', depress = False)
                        props.index = input_index
                        col = box.column(align=True)
                            
                        if modifier[input_index] == gn_bool_version(0):
                            col.prop(modifier, '["Input_20"]', text="Thickness")
                            col.prop(modifier, '["Input_21"]', text="Radius")
                            col.prop(modifier, '["Input_22"]', text="Angle")
                        else:
                            col.prop_search(modifier, '["Input_24"]', bpy.data, "objects", text="", icon="OBJECT_DATA")
                        

                    # RINGS
                    box = layout.box()
                    input_index = "Input_30"
                    if modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='Rings', depress = True)
                    else:
                        box.scale_y = 2
                        props = box.operator('switch.button', text='Rings', depress = False)
                    props.index = input_index
                    if modifier[input_index] == gn_bool_version(1):
                            col = box.column(align=True)
                            col.prop(modifier, '["Input_27"]', text="Spacing")
                            col.prop(modifier, '["Input_25"]', text="Length")
                            col.prop(modifier, '["Input_26"]', text="Thickness")


                    # MATERIAL
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Material", icon = "MATERIAL")
                    box.prop_search(modifier, '["Input_33"]', bpy.data, "materials", text="Rings", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_32"]', bpy.data, "materials", text="Fix", icon="MATERIAL")
                    box.prop_search(modifier, '["Input_31"]', bpy.data, "materials", text="Curves", icon="MATERIAL")

                elif mo_type == "array":
                    modifier_header_basic(col)
                    array_modifier = obj.modifiers[modifiers[0]]
                    array_type = modifiers[1]

                    if array_type == 'LINE':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_4"]', text = "Count")
                        col.prop(array_modifier, '["Input_3"]', text = "Constant Offset")
                        col.prop(array_modifier, '["Input_5"]', text = "Relative Offset")

                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_6"]', text = "Position")
                        box.prop(array_modifier, '["Input_7"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_8"]', text = "Scale")
                        box.prop(array_modifier, '["Input_9"]', text = "Seed")

                    if array_type == 'GRID':
                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_2"]', text = "Count X")
                        col.prop(array_modifier, '["Input_9"]', text = "Count Y")
                        box = layout.box()
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_3"]', text = "Constant Offset X")
                        col.prop(array_modifier, '["Input_11"]', text = "Constant Offset Y")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_4"]', text = "Relative Offset X")
                        col.prop(array_modifier, '["Input_10"]', text = "Relative Offset Y")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_12"]', text = "Midlevel X")
                        col.prop(array_modifier, '["Input_13"]', text = "Midlevel Y")

                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_5"]', text = "Position")
                        box.prop(array_modifier, '["Input_6"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_8"]', text = "Scale")
                        box.prop(array_modifier, '["Input_7"]', text = "Seed")

                    if array_type == 'CIRCLE':
                        col = layout.column(align=True)
                        Double_Row_Switch(col, array_modifier, "Input_19", "Count", "Distance")
                        if array_modifier["Input_19"] == True:
                            col.prop(array_modifier, '["Input_20"]', text = "Constant Distance")
                            col.prop(array_modifier, '["Input_2"]', text = "Circle Resolution")
                        else:
                            col.prop(array_modifier, '["Input_2"]', text = "Count")
                        col.prop(array_modifier, '["Input_4"]', text = "Radius")

                        col.separator(factor = 0.4)
                        col.prop(array_modifier, '["Input_3"]', text = "Ring Count")
                        col.prop(array_modifier, '["Input_8"]', text = "Ring Offset")
                        col.prop(array_modifier, '["Input_9"]', text = "Ring Offset Z")

                        col.separator(factor = 2)
                        row=col.row()
                        row.prop(array_modifier, '["Input_14"]', text = "Rotation")
                        col.prop(array_modifier, '["Input_10"]', text = "Align to Center", toggle=True)

                        box = layout.box()
                        box.label(text="Random")
                        row=box.row()
                        row.prop(array_modifier, '["Input_17"]', text = "Position")
                        row=box.row()
                        row.prop(array_modifier, '["Input_15"]', text = "Rotation")
                        col = box.column(align=True)
                        col.prop(array_modifier, '["Input_16"]', text = "Scale")
                        box.prop(array_modifier, '["Input_18"]', text = "Seed")
                        
                    if array_type == 'CURVE':
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        input_index = "Input_4"
                        if array_modifier[input_index] == gn_bool_version(1):
                            props = row.operator('switch.button', text='Length', depress = False)
                            props = row.operator('switch.button', text='Count', depress = True)
                            col.prop(array_modifier, '["Input_6"]', text = "Count")
                        else:
                            props = row.operator('switch.button', text='Length', depress = True)
                            props = row.operator('switch.button', text='Count', depress = False)
                            col.prop(array_modifier, '["Input_5"]', text = "Length")
                        props.index = input_index

                        col.label(text="Target :")
                        col.prop_search(array_modifier, '["Input_2"]', bpy.data, "objects", text="", icon="OBJECT_DATA")

                        col = layout.column(align=True)
                        col.prop(array_modifier, '["Input_3"]', text = "Rotation")
                        col.prop(array_modifier, '["Input_14"]', text = "Scale")
                        box = layout.box()
                        box.label(text="Random")
                        box.prop(array_modifier, '["Input_7"]', text = "Random Position")
                        box.prop(array_modifier, '["Input_8"]', text = "Random Rotation")
                        box.prop(array_modifier, '["Input_9"]', text = "Random Scale")
                        box.prop(array_modifier, '["Input_12"]', text = "Seed")

                        box = layout.box()
                        box.prop(array_modifier, '["Input_10"]', text = "Align to Vector")
                        box = box.row(align=True)
                        box.prop(array_modifier, '["Input_11"]', text = "Vector")

                    if array_type == 'CURVE_DRAW':
                        col = layout.column(align=True)
                        col.prop_search(array_modifier, '["Input_2"]', bpy.data, "collections", text="Target", icon="OUTLINER_COLLECTION")
                        
                        
                        # ui_type, modifier, index, name_a, name_b
                        Double_Row_Switch(col, array_modifier, "Input_4", "Length", "Count")
                        if array_modifier["Input_4"] == gn_bool_version(1):
                            col.prop(array_modifier, '["Input_6"]', text = "Count")
                        else:
                            col.prop(array_modifier, '["Input_5"]', text = "Length")
                        box = layout.box()
                        box.label(text="Rotation")
                        row = box.row(align=True)
                        row.prop(array_modifier, '["Input_3"]', text = "")
                        box.label(text="Position")
                        row = box.row(align=True)
                        row.prop(array_modifier, '["Input_15"]', text = "")
                        box.prop(array_modifier, '["Input_10"]', text = "Align to Curve")
                        col = box.column(align=True)
                        col.label(text="Scale")
                        col.prop(array_modifier, '["Input_9"]', text = "Min")
                        col.prop(array_modifier, '["Input_14"]', text = "Max")
                        box = layout.box()
                        box.label(text="Random")
                        box.label(text="Position")
                        row = box.row(align=True)
                        row.prop(array_modifier, '["Input_7"]', text = "")
                        box.label(text="Rotation")
                        row = box.row(align=True)
                        row.prop(array_modifier, '["Input_8"]', text = "")
                        row = box.row(align=True)
                        row.prop(array_modifier, '["Input_12"]', text = "Seed")

                elif mo_type == "scatter":
                    
                    ######################################
                    # MAIN SETTINGS
                    ######################################
                    modifier_header_basic(col)
                    col.operator("rename.layer", text= "Rename Layer", icon = 'GREASEPENCIL')
                    scatter_modifier = obj.modifiers[modifiers[0]].node_group.nodes[modifiers[1]]
                    
                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(scatter_modifier.inputs[2], 'default_value', text = "Distance Min")
                    row = col.row(align=True)
                    row.prop(scatter_modifier.inputs[3], 'default_value', text = "Density Max")
                    tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                    tips.message = 'Keep this value as low as possible to preserve performance.'
                    col.prop(scatter_modifier.inputs[4], 'default_value', text = "% Viewport Display")
                    col.prop(scatter_modifier.inputs[5], 'default_value', text = "Align Normal")
                    col.prop(scatter_modifier.inputs[6], 'default_value', text = "Seed")

                    ######################################
                    # TOOLS
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.enabled = (bpy.context.mode == 'OBJECT')
                    col_bt.prop(bagapie_pref, 'scatter_tools', text="Tools", icon='TOOL_SETTINGS', toggle=True)

                    if bagapie_pref.scatter_tools:
                        box = layout.box()
                        col = box.column(align=True)
                        col.scale_y = 2

                        col.separator(factor = 0.4)
                        row = col.row(align=True)
                        if bagapie_pref.asset_source:
                            row.operator("add.asset", text= "Add Assets", icon = 'ADD')
                            tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                            tips.message = 'Selected objects will be added to the current scatter layer'
                        else: 
                            imp = row.operator("bagapie.asset_browser", text= "Add Assets", icon = 'ADD')
                            imp.import_mode= 'AddAssets'
                            tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                            tips.message = 'Selected assets in the asset browser will be added to the current scatter layer'

                        row = col.row(align=True)
                        row.scale_y = 0.6
                        split = row.split(factor=0.25, align=True)
                        split.label(text="Source :")
                        split.prop(bagapie_pref, 'asset_source', text = "View 3D",  toggle = True)
                        split.prop(bagapie_pref, 'asset_source', text = "Asset Browser",  toggle = True, invert_checkbox=True)
                        tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                        tips.message = 'Select the source of the object you want to add to the current scatter layer'

                        col.separator(factor = 0.3)
                        row = col.row(align=True)
                        row.operator("remove.asset", text= "Remove Assets", icon = 'REMOVE')
                        tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                        tips.message = 'Select the asset(s) you want to remove from the active layer (surface select last)'

                        col.separator(factor = 0.4)
                        
                        if obj.modifiers[modifiers[0]].node_group.nodes.get('BagaPie_Camera_Culling'):
                            row = col.row(align=True)
                            if len(scatter_modifier.inputs[24].links) > 0:
                                props = row.operator('use.cameracullingonlayer', text='Camera Culling', depress = True, icon = 'OUTLINER_OB_CAMERA')
                            else:
                                props = row.operator('use.cameracullingonlayer', text='Use Camera Culling', depress = False, icon = 'CAMERA_DATA')
                            props.index = 24
                            
                        col_contect = col.column(align=True)
                        col_contect.scale_y = 0.6
                        col_contect.label(text="Layer Collection :")
                        col_contect.prop(scatter_modifier.inputs[1], 'default_value', text = "")

                        Draw_Scatter_Layer_Content(box, scatter_modifier)

                        row = box.row(align=True)
                        row.operator("use.proxyonassets", text= "Proxy All", icon = 'RESTRICT_VIEW_OFF').use_proxy = True
                        row.operator("use.proxyonassets", text= "Proxy All", icon = 'RESTRICT_VIEW_ON').use_proxy = False

                        box.operator("select.content", text= "Select All Assets", icon = 'RESTRICT_SELECT_OFF')

                    ######################################
                    # PAINT MODE
                    ######################################
                    if bpy.context.object.mode == 'OBJECT':
                        col = layout.column(align=True)
                        col.scale_y = 2
                        row = col.row(align=True)
                        row.operator("switch.mode", text= "Paint !", icon = 'BRUSH_DATA')
                        if scatter_modifier.inputs[26].default_value:
                            props = row.operator('switch.boolnode', text='', depress = True, icon = 'ARROW_LEFTRIGHT')
                        else:
                            props = row.operator('switch.boolnode', text='', depress = False, icon = 'ARROW_LEFTRIGHT')
                        props.index = 26

                    if bpy.context.object.mode == 'WEIGHT_PAINT':
                        col = layout.column()
                        col.scale_y = 2
                        col.operator("switch.mode", text="Exit Paint Mode", icon = 'FILE_PARENT')
                        col = layout.column()
                        # col.scale_y = 1.5
                        box=col.box()
                        box.label(text="Painting :", icon = "BRUSH_DATA")
                        box.operator("clean.paint", text= "Clear Paint", icon = 'FILE_REFRESH')
                        box.operator("invert.weight", text= "Invert Paint", icon = 'ARROW_LEFTRIGHT')
                        if bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname == "builtin_brush.Draw":
                            draw_brush = bpy.data.brushes.get("Draw")
                            if draw_brush:
                                box.label(text="Brush Profile :")
                                box.prop(draw_brush, "curve_preset", text="")


                        mo_main = obj.modifiers[modifiers[0]]
                        node_group = mo_main.node_group
                        socket_id = scatter_modifier.inputs[25].links[0].from_socket.identifier

                        for i in node_group.interface.items_tree:
                            if i.in_out == 'INPUT':
                                if i.socket_type == 'NodeSocketFloat':
                                    identifier=i.identifier
                                    if socket_id == identifier:
                                        box.label(text="Vertex Group :")
                                        box.prop_search(
                                            mo_main, 
                                            f'["{identifier}_attribute_name"]',
                                            obj, 
                                            "vertex_groups",
                                            text=""
                                        )

                        paint_invert_mode = scatter_modifier.inputs[26].default_value
                        if bpy.app.version >= (5, 0, 0):
                            weight = bpy.context.scene.tool_settings.weight_paint.brush.weight
                        else:
                            weight = bpy.context.scene.tool_settings.unified_paint_settings.weight
                        add_depress = (paint_invert_mode and weight >= 0.5) or (not paint_invert_mode and weight < 0.5)
                        remove_depress = not add_depress

                        row = box.row(align=True)
                        row.operator("invert.paint", text="Add", depress=add_depress, icon='ADD')
                        row.operator("invert.paint", text="Remove", depress=remove_depress, icon='REMOVE')

                        box = box.box()
                        box.scale_y = 0.3
                        box.separator(factor = 0.5)
                        box.label(text="Tips", icon = "INFO")
                        box.separator(factor = 1)
                        box.label(text="Paint resolution depend")
                        box.label(text="on your mesh topology !")
                        box.separator(factor = 1)
                        box.label(text="If necessary,")
                        box.label(text="subdivide your surface.")

                    ######################################
                    # POSITION / ROTATION / SCALE SETTINGS
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.prop(bagapie_pref, 'scatter_posrot', text = "Transform", toggle = True)

                    if bagapie_pref.scatter_posrot:
                        box = layout.box()
                        box = box.column(align=True)
                        row = box.row()
                        row.label(text="Position")
                        row = box.row()
                        row.prop(scatter_modifier.inputs[7], 'default_value', text = "")
                        row = box.row()
                        row.label(text="Rotation")
                        box = box.column(align=False)
                        row = box.row()
                        row.prop(scatter_modifier.inputs[8], 'default_value', text = "")
                        row = box.row()
                        row = box.column(align=True)
                        row.prop(scatter_modifier.inputs[9], 'default_value', text = "Scale Min")
                        row.prop(scatter_modifier.inputs[10], 'default_value', text = "Scale Max")

                    ######################################
                    # RANDOM SETTINGS
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.prop(bagapie_pref, 'scatter_random', text = "Randomize Transform", toggle = True)

                    if bagapie_pref.scatter_random:
                        box = layout.box()
                        box = box.column(align=True)
                        row = box.row()
                        row.label(text="Position :")
                        row.label(text="X")
                        row.label(text="Y")
                        row.label(text="Z")
                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Min")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[11], 'default_value', text = "")

                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Max")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[12], 'default_value', text = "")

                        box.separator(factor = 1)
                        row = box.row()
                        row.label(text="Rotation :")

                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Min")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[13], 'default_value', text = "")

                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Max")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[14], 'default_value', text = "")

                        box.separator(factor = 1)
                        row = box.row()
                        row.label(text="Scale :")

                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Min")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[15], 'default_value', text = "")

                        row = box.row()
                        split=row.split(factor=0.15)
                        split.label(text="Max")
                        row = split.row()
                        row.prop(scatter_modifier.inputs[16], 'default_value', text = "")

                    ######################################
                    # TEXTURE SETTINGS
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.prop(bagapie_pref, 'scatter_mask', text = "Mask", toggle = True)

                    if bagapie_pref.scatter_mask:
                        box = layout.box()
                        row = box.row(align=True)
                        row.label(text="Texture Mask")
                        row.operator("bagapie.texturemask_copy", text="", icon="COPYDOWN")
                        row.operator("bagapie.texturemask_paste", text="", icon="PASTEDOWN")
                        col = box.column(align=True)
                        col.prop(scatter_modifier.inputs[17], 'default_value', text = "Fac")
                        col.prop(scatter_modifier.inputs[18], 'default_value', text = "Scale")
                        col.prop(scatter_modifier.inputs[19], 'default_value', text = "Offset")
                        col.prop(scatter_modifier.inputs[20], 'default_value', text = "Smooth")
                        col.label(text="Position :")
                        row = col.row()
                        row.prop(scatter_modifier.inputs[27], 'default_value', text = "")
                        col.prop(scatter_modifier.inputs[28], 'default_value', text = "Invert Mask")

                    ######################################
                    # TUTORIAL & DOC
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.prop(bagapie_pref, 'scatter_tuto', text = "Tutorial", toggle = True)

                    if bagapie_pref.scatter_tuto:
                        box = layout.box()
                        col = box.column(align=True)
                        col.operator("wm.url_open", text="Scatter Tutorial", icon = 'PLAY').url = "https://youtu.be/oMKetYzkAI0?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"
                        col.operator("wm.url_open", text="Documentation", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"

                    ######################################
                    # GEOPACK EXPORT
                    ######################################
                    col_bt = layout.column()
                    col_bt.scale_y = 2
                    col_bt.prop(bagapie_pref, 'scatter_geopack_export', text = "Save in GeoPack", toggle = True)

                    if bagapie_pref.scatter_geopack_export:
                        box = layout.box()
                        col = box.column(align=True)
                        col_gp = col.column()
                        col_gp.scale_y = 2
                        col_gp.operator("bagapie.geopack_create_modifier", text="Save Scatter in GeoPack")
                        col.operator("wm.url_open", text="Create Preset Tutorial", icon = 'PLAY').url = "https://youtu.be/SbOvA8Yzdrw?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu"
                        col.prop(bagapie_pref, 'geopack_render_generate', text = "Generate Preview Icon", toggle = True, icon = 'IMAGE_DATA')
                        if bagapie_pref.geopack_render_generate == True:
                            col.prop(bagapie_pref, 'geopack_render_use_current_world', text = "Lighting : Use Current World")

                        col.label(text="What it does :")
                        col.label(text=" - All scatter layers will be saved")
                        col.label(text=" - Re-use scatter like a preset")
                        col.label(text=" - Can be Exported as .geopack file")
                        col.label(text=" - Assets stored in the pack")
                        col.label(text=" - CamCull & Effectors ignored")
                        if bagapie_pref.geopack_render_generate == True:
                            col.label(text=" - Preview stored in pack")
                            col.label(text=" - Preview from current view")
                            col.label(text=" - Preview from active object")
                            col.label(text=" - Preview can be change in Pref")
                            res = bagapie_pref.geopack_render_resolution
                            samples = bagapie_pref.geopack_render_samples
                            col.label(text=f' - Preview {res}px/{samples} samples, see pref')

                elif mo_type == "displace":
                    modifier_header_basic(col)
                    displace_subdiv = obj.modifiers[modifiers[0]]
                    displace_disp = obj.modifiers[modifiers[1]]
                    texture = bpy.data.textures[modifiers[2]]

                    box = layout.box()# SUBDIVISION
                    box.label(text="Subdivision")
                    box.prop(displace_subdiv, 'subdivision_type', text="Type")
                    box = box.column(align=True)
                    box.prop(displace_subdiv, 'levels', text="Subdivision")
                    box.prop(displace_subdiv, 'render_levels', text="Subdivision Render")

                    box = layout.box()# DISPLACEMENT
                    box.label(text="Displace")
                    box.prop(displace_disp, 'direction', text="Direction")
                    box = box.column(align=True)
                    box.prop(displace_disp, 'strength', text="Strength")
                    box.prop(displace_disp, 'mid_level', text="Midlevel")
                    box = layout.box()

                    box.label(text="Texture")# TEXTURE
                    box.prop(texture, 'type', text="Type")
                    if texture.type == 'IMAGE':
                        box.label(text="Go in Texture tab.")
                    box.prop(displace_disp, 'texture_coords', text="Mapping")
                    if displace_disp.texture_coords == 'OBJECT':
                        box.prop(displace_disp, 'texture_coords_object', text="Object")
                    box = box.column(align=True)
                    box.prop(texture, 'noise_scale', text="Scale")
                    box.prop(texture, 'intensity', text="Brightness")
                    box.prop(texture.color_ramp.elements[0], 'position', text="Ramp Min")
                    box.prop(texture.color_ramp.elements[1], 'position', text="Ramp Max")

                elif mo_type == "scatterpaint":
                    modifier_header_basic(col)

                    col = layout.column(align=True)
                    col.scale_y = 2.0

                    if bpy.context.object.mode == 'OBJECT':
                        col.operator("switch.mode", text= "Paint !")

                    if bpy.context.object.mode == 'WEIGHT_PAINT':
                        
                        if bpy.app.version >= (5, 0, 0):
                            weight = bpy.context.scene.tool_settings.weight_paint.brush.weight
                        else:
                            weight = bpy.context.scene.tool_settings.unified_paint_settings.weight
                        if weight < 1:
                            col.operator("invert.paint", text="ADD")
                        else:
                            col.operator("invert.paint", text="REMOVE")

                        col.scale_y = 1
                        col.operator("clean.paint", text= "CLEAN PAINT")
                        col.operator("invert.weight", text= "INVERT PAINT")

                        col = layout.column()
                        col.scale_y = 2
                        col.operator("switch.mode", text="EXIT !")

                    scatter_modifier = obj.modifiers.get("BagaScatter")
                    scatt_nde_group = scatter_modifier.node_group
                    scatt_nde_main = scatt_nde_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.prop(scatt_nde_main.inputs[1], 'default_value', text = "Source Collection")
                    col.prop(scatt_nde_main.inputs[2], 'default_value', text = "Distance Min")
                    col.prop(scatt_nde_main.inputs[3], 'default_value', text = "Density")
                    col.prop(scatt_nde_main.inputs[4], 'default_value', text = "% Viewport Display")


                    box = layout.box()
                    box = box.column(align=True)
                    box.prop(scatt_nde_main.inputs[7], 'default_value', text = "Random Position")
                    box.prop(scatt_nde_main.inputs[8], 'default_value', text = "Random Rotation")
                    box.prop(scatt_nde_main.inputs[11], 'default_value', text = "Align Z")
                    box.prop(scatt_nde_main.inputs[9], 'default_value', text = "Scale Min")
                    box.prop(scatt_nde_main.inputs[10], 'default_value', text = "Scale Max")
                    box.prop(scatt_nde_main.inputs[5], 'default_value', text = "Seed")

                    box.label(text="Current Layer :")
                    box.prop(obj.vertex_groups, 'active_index', text = obj.vertex_groups.active.name)

                elif mo_type == "curvearray":
                    modifier_header_basic(col)
                    arraycurve_array = obj.modifiers[modifiers[0]]
                    arraycurve_curve = obj.modifiers[modifiers[1]]

                    col = layout.column()
                    col.prop(arraycurve_curve, 'deform_axis', text="Axis")
                    box = layout.box()
                    box.prop(arraycurve_array, 'use_relative_offset', text="Use Relative Offset")
                    box.prop(arraycurve_array, 'relative_offset_displace', text="Ralative Offset")
                    box = layout.box()
                    box.prop(arraycurve_array, 'use_constant_offset', text="Use Constant Offset")
                    box.prop(arraycurve_array, 'constant_offset_displace', text="Constant Offset")

                elif mo_type == "window":
                    modifier_header_basic(col)

                    if modifiers[6] == "win":
                        window_weld = obj.modifiers[modifiers[0]]
                        window_disp = obj.modifiers[modifiers[1]]
                        window_wire = obj.modifiers[modifiers[2]]
                        window_bevel = obj.modifiers[modifiers[3]]

                        box = layout.box()
                        box.prop(window_disp, 'strength', text="Offset")
                        box.prop(window_wire, 'thickness', text="Window Size")
                        box.prop(window_wire, 'offset', text="Window Offset")
                        box.prop(window_bevel, 'width', text="Window Bevel")
                        box.prop(window_weld, 'merge_threshold', text="Merge by Distance")


                        col = layout.column()
                        col.scale_y = 1.5
                        active_ob = bpy.context.active_object
                        if bpy.context.object.mode == 'OBJECT' and active_ob == obj:
                            col.operator("bool.mode", text= "More Window !")
                        elif bpy.context.object.mode == 'EDIT' and active_ob == obj:
                            col.operator("bool.mode", text= "EXIT")
                        else:
                            col.label(text="Selects the bounding box of the window")


                    elif modifiers[6] == "wall":

                        window = bpy.data.objects[modifiers[7]]

                        window_weld = window.modifiers[modifiers[1]]
                        window_disp = window.modifiers[modifiers[2]]
                        window_wire = window.modifiers[modifiers[3]]
                        window_bevel = window.modifiers[modifiers[4]]

                        box = layout.box()
                        box.prop(window_disp, 'strength', text="Offset")
                        box.prop(window_wire, 'thickness', text="Window Size")
                        box.prop(window_wire, 'offset', text="Window Offset")
                        box.prop(window_bevel, 'width', text="Window Bevel")
                        box.prop(window_weld, 'merge_threshold', text="Merge by Distance")

                elif mo_type == "pointeffector":
                    modifier_header_basic(col)
                    effector_modifier = obj.modifiers[modifiers[0]]
                    effector_nde = effector_modifier.node_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.label(text="Effector Collection :", icon = "OUTLINER_COLLECTION")
                    col.prop_search(effector_nde.inputs[0], 'default_value', bpy.data, "collections", text="", icon="OUTLINER_COLLECTION")
                    col.separator(factor = 1)
                    col.prop(effector_nde.inputs[1], 'default_value', text = "Distance Min")
                    col.prop(effector_nde.inputs[2], 'default_value', text = "Distance Max")
                    col.prop(effector_nde.inputs[3], 'default_value', text = "Density")

                elif mo_type == "camera":
                    modifier_header_basic(col)
                    effector_modifier = obj.modifiers[modifiers[0]]
                    effector_nde = effector_modifier.node_group.nodes.get(modifiers[1])

                    col = layout.column(align=True)
                    col.scale_y = 1.2
                    col.label(text="Camera :")
                    col.prop_search(effector_nde.inputs[0], 'default_value', bpy.data, "objects", text="", icon="VIEW_CAMERA")
                    col.separator(factor = 1)
                    col.prop(effector_nde.inputs[1], 'default_value', text = "X Ratio")
                    col.prop(effector_nde.inputs[2], 'default_value', text = "Y Ratio")
                    col.prop(effector_nde.inputs[5], 'default_value', text = "Offset")
                    
                    box = layout.box()
                    box = box.column(align=True)
                    box.label(text="Tips", icon = "INFO")
                    box.label(text="Culling resolution depend")
                    box.label(text="on your surface resolution !")
                    box.separator(factor = 2)
                    box.label(text="If necessary,")
                    box.label(text="subdivide your surface.")

                elif mo_type == "boolean":
                    modifier_header_basic(col)
                    box = layout.box()

                    box.label(text="Boolean Type")
                    box.prop(obj.modifiers[modifiers[0]], 'operation', text="")
                    box.prop(obj.modifiers[modifiers[0]], 'solver', text="")
                    if obj.modifiers[modifiers[0]].solver == 'EXACT':
                        box = box.row(align = True)
                        box.prop(obj.modifiers[modifiers[0]], 'use_self', text="Use self")
                        box.prop(obj.modifiers[modifiers[0]], 'use_hole_tolerant', text="Hole Tolerant")

                    box = layout.box()
                    box.label(text="Boolean Target")
                    box = box.column(align = True)
                    box.prop(obj.modifiers[modifiers[1]], 'segments', text="Bevel Segments")
                    box.prop(obj.modifiers[modifiers[1]], 'width', text="Bevel Size")

                    bool_obj = bpy.data.objects[modifiers[5]]

                    box = layout.box()
                    box.label(text="Boolean Object")
                    box = box.column(align = True)
                    box.prop(bool_obj.modifiers[modifiers[3]], 'segments', text="Bevel Segments")
                    box.prop(bool_obj.modifiers[modifiers[3]], 'width', text="Bevel Size")
                    box.prop(bool_obj.modifiers[modifiers[6]], 'strength', text="Displace")

                    box = box.column(align = False)
                    col = box.column()
                    if bool_obj.modifiers[modifiers[4]].show_render:
                        box.operator("solidify.visibility", text= "Disable Solidify")
                    else:
                        box.operator("solidify.visibility", text= "Use Solidify")
                    box = box.column(align = True)  
                    box.prop(bool_obj.modifiers[modifiers[4]], 'thickness', text="Solidify")
                    box.prop(bool_obj.modifiers[modifiers[4]], 'offset', text="Solidify Offset")
                    box = box.row(align = True)
                    box.label(text="Mirror XYZ")
                    box.prop(bool_obj.modifiers[modifiers[2]], 'use_axis', text="")
                    
                    col = layout.column()
                    col.scale_y = 2.0
                    active_ob = bpy.context.active_object
                    if bpy.context.object.mode == 'OBJECT' and active_ob == obj:
                        col.operator("bool.mode", text= "More Boolean !")
                    elif bpy.context.object.mode == 'EDIT' and active_ob == obj:
                        col.operator("bool.mode", text= "EXIT")

                elif mo_type == "ivy":
                    modifier_header_basic(col)
                    ivy_modifier = obj.modifiers[modifiers[0]]
                    box = layout.box()
                    box = box.column(align=True)
                    box.scale_y = 1.5
                    box.operator("bagapie.addvertcursor", text="Add Ivy to 3D Cursor")
                    row=box.row(align=True)
                    row.operator("bagapie.addobjecttarget", text="Target", icon = 'ADD')
                    row.operator("bagapie.removeobjecttarget", text="Target", icon = 'REMOVE')
                    box = layout.box()

                    box.label(text="Ivy")
                    row = box.row(align=True)
                    input_index = "Input_23"
                    if ivy_modifier[input_index] == gn_bool_version(1):
                        props = row.operator('switch.button', text='Spiral', depress = False, icon = 'MOD_DASH')
                    else:
                        props = row.operator('switch.button', text='Spiral', depress = True, icon = 'MOD_DASH')
                    props.index = input_index
                    if ivy_modifier[input_index] == gn_bool_version(0):
                        props = row.operator('switch.button', text='Grid Project', depress = False, icon = 'VIEW_ORTHO')
                    else:
                        props = row.operator('switch.button', text='Grid Project', depress = True, icon = 'VIEW_ORTHO')
                    props.index = input_index
                    input_index = "Input_18"
                    if ivy_modifier[input_index] == gn_bool_version(1):
                        props = box.operator('switch.button', text='View Guide', depress = True, icon = 'HIDE_OFF')
                    else:
                        props = box.operator('switch.button', text='View Guide', depress = False, icon = 'HIDE_ON')
                    props.index = input_index
                    box = box.column(align=True)
                    
                    box.prop(ivy_modifier, '["Input_3"]', text = "Radius")
                    if not ivy_modifier['Input_23']:
                        box.prop(ivy_modifier, '["Input_5"]', text = "Height")
                        box.prop(ivy_modifier, '["Input_6"]', text = "Loop")
                    box.prop(ivy_modifier, '["Input_21"]', text = "Gravity")
                    box.prop(ivy_modifier, '["Input_19"]', text = "Scale")
                    box.prop(ivy_modifier, '["Input_2"]', text = "Resolution")

                    box = layout.box()
                    box = box.column(align=True)
                    box.prop(ivy_modifier, '["Input_10"]', text = "Density")
                    box.prop(ivy_modifier, '["Input_20"]', text = "Decimate")

                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.prop(ivy_modifier, '["Input_7"]', text = "Random Position")
                    box.prop(ivy_modifier, '["Input_14"]', text = "Emission Area")
                    box.prop(ivy_modifier, '["Input_11"]', text = "Surface Offset")
                    box.prop(ivy_modifier, '["Input_8"]', text = "Scale")
                    box.label(text="Ivy Random Position")
                    box = box.row(align=True)
                    box.prop(ivy_modifier, '["Input_12"]', text = "")
                    
                    box = layout.box()
                    box.label(text="Collections", icon = "INFO")
                    box.prop_search(ivy_modifier, '["Input_9"]', bpy.data, "collections", text="Target", icon="OUTLINER_COLLECTION")
                    box.prop_search(ivy_modifier, '["Input_16"]', bpy.data, "collections", text="Asset", icon="OUTLINER_COLLECTION")
                    box.prop_search(ivy_modifier, '["Input_17"]', bpy.data, "collections", text="Emitter", icon="OUTLINER_COLLECTION")

                elif mo_type == "pointsnapinstance":
                    modifier_header_basic(col)
                    psi_modifier = obj.modifiers[modifiers[0]]
                    col = layout.column(align=True)
                    col.scale_y=2
                    col.operator("bagapie.pointsnapinstance", text= "Add Instances")
                    col = layout.column(align=True)
                    col.label(text="ESCAPE to Stop")

                    col = layout.column(align=True)
                    box = layout.box()
                    box.label(text="Main")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_9"]', text = "Offset Z")
                    box.prop(psi_modifier, '["Input_8"]', text = "Align Normal")
                    box = layout.box()
                    box.label(text="Random")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_5"]', text = "Random Rotation")
                    box.prop(psi_modifier, '["Input_6"]', text = "Scale Min")
                    box.prop(psi_modifier, '["Input_7"]', text = "Scale Max")
                    
                    box = layout.box()
                    box.label(text="Source info", icon = "INFO")
                    box.prop_search(psi_modifier, '["Input_3"]', bpy.data, "objects", text="Target", icon="OBJECT_DATA")
                    box.prop_search(psi_modifier, '["Input_4"]', bpy.data, "collections", text="Instances", icon="OUTLINER_COLLECTION")                    

                elif mo_type == "grass":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Grass Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                            elif node.name == modifiers[1]:
                                shader_node = node
                            elif node.name == modifiers[2]:
                                shader_node = node

                        if shader_node.name.startswith('BagaPie_Moss'):
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[0], 'default_value', text = "Saturation")

                        elif shader_node.name.startswith('BagaPie_LP_Plant'):
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[2], 'default_value', text = "AO Distance")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[3], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[4], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[7], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[8], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Random Saturation")

                        else:
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Saison")
                            if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                box.label(text="Season value up to 0.9", icon = 'ERROR')
                                box.label(text="This value add transparency.")
                                box.label(text="May increase render time !")
                                box.label(text="Decrease Season or Random Season")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")

                elif mo_type == "plant":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Plant Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        disp = False
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[1]:
                                shader_node = node
                            elif node.name == modifiers[2]:
                                shader_node = node

                        if shader_node.name == "BagaPie_LP_Plant":
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "Color")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[2], 'default_value', text = "AO Distance")
                            if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                if bpy.context.scene.eevee.use_gtao:
                                    box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                            box.separator(factor = 1)
                            box.prop(shader_node.inputs[3], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[4], 'default_value', text = "")
                            box.separator(factor = 1)
                            box.prop(shader_node.inputs[6], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[7], 'default_value', text = "")
                            box.separator(factor = 1)                            
                            box.prop(shader_node.inputs[8], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Random Saturation")

                        elif shader_node.name.startswith("BagaPie_LP_Tree_Leaf"):
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[2], 'default_value', text = "Subsurface")
                            box.prop(shader_node.inputs[3], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[4], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                            box.prop(shader_node.inputs[6], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[8], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[9], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Random Saturation")

                        
                        elif shader_node.name.startswith("BagaPie_V2"):
                            if "Desert" in shader_node.name:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    idx_input = 4
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 5
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 7
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 8
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 9
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 10
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 11
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 12
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                            elif "Bark" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                box = box.column(align=True)
                                idx_input = 4
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 5
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 11
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 12
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 9
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                idx_input = 10
                                box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                            else: 
                                box = layout.box()
                                box.label(text="Material " + str(index))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                    box.label(text="Season value up to 0.9", icon = 'ERROR')
                                    box.label(text="This value add transparency.")
                                    box.label(text="May increase render time !")
                                    box.label(text="Decrease Season or Random Season")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                                box.prop(shader_node.inputs[12], 'default_value', text = "Alpha")

                        elif disp is True:
                            box = layout.box()
                            box.label(text="Material " + str(index))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                            box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                            if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                box.label(text="Season value up to 0.9", icon = 'ERROR')
                                box.label(text="This value add transparency.")
                                box.label(text="May increase render time !")
                                box.label(text="Decrease Season or Random Season")
                            box.separator(factor = 0.5)
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                            box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")

                elif mo_type == "rock":
                    material_slots = obj.material_slots
                    col.label(text="Rock Shader :")
                    
                    for m in material_slots:
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                        
                        if shader_node.name.startswith("BagaPie_V2"):
                            if "Rock" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                inp = shader_node.inputs

                                idx_input = [13,14,15,16]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[17], 'default_value', text = "Tint")
                                box.prop(shader_node.inputs[18], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                idx_input = [4,5]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.label(text="Bump")
                                box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                                box.prop(shader_node.inputs[7], 'default_value', text = "Intensity")
                                box.label(text="Ambient Occlusion")
                                box.prop(shader_node.inputs[6], 'default_value', text = "AO (Map)")
                                if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                    if bpy.context.scene.eevee.use_gtao:
                                        box.label(text="AO disabled")
                                        box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                                box.prop(shader_node.inputs[10], 'default_value', text = "AO Distance")
                                box.prop(shader_node.inputs[11], 'default_value', text = "AO Intensity")
                        elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[0], 'default_value', text = "AO")
                            box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                            box.prop(shader_node.inputs[8], 'default_value', text = "AO Tint")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                            box.prop(shader_node.inputs[3], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")
                        else:
                            box = layout.box()
                            box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                            box = box.column(align=True)
                            box.prop(shader_node.inputs[1], 'default_value', text = "Saturation")
                            box.prop(shader_node.inputs[2], 'default_value', text = "Random Saturation")
                            box.prop(shader_node.inputs[3], 'default_value', text = "Brightness")
                            box.prop(shader_node.inputs[4], 'default_value', text = "Random Brightness")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[6], 'default_value', text = "Tint")
                            box.prop(shader_node.inputs[5], 'default_value', text = "")
                            box.separator(factor = 0.5)
                            box.prop(shader_node.inputs[7], 'default_value', text = "Specular")
                            box.prop(shader_node.inputs[8], 'default_value', text = "Roughness")

                            box.label(text="Bump")
                            box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                            box.prop(shader_node.inputs[13], 'default_value', text = "Intensity")
                            box.label(text="Ambient Occlusion")
                            if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                if not bpy.context.scene.eevee.use_gtao:
                                    box.label(text="AO disabled")
                                    box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                            box.prop(shader_node.inputs[14], 'default_value', text = "Intensity")
                            box.prop(shader_node.inputs[15], 'default_value', text = "Distance")

                elif mo_type == "tree":
                    material_slots = obj.material_slots
                    index = 0
                    col.label(text="Tree Shader :")
                    for m in material_slots:
                        index += 1
                        material = m.material
                        nodes = material.node_tree.nodes
                        disp = False
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[1] and modifiers[1] != "":
                                shader_node = node
                                disp = True
                            elif node.name == modifiers[2] and modifiers[2] != "":
                                shader_node = node
                                disp = True
                        
                        # disp = DISPLAY !
                        if disp is True:
                            if shader_node.name.startswith("BagaPie_LP_Tree_Leaf"):
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                                box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[2], 'default_value', text = "Subsurface")
                                box.prop(shader_node.inputs[3], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[4], 'default_value', text = "Tint Intensity")
                                box.prop(shader_node.inputs[5], 'default_value', text = "Random Tint")
                                box.prop(shader_node.inputs[6], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[8], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[9], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Random Saturation")

                            elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[0], 'default_value', text = "AO White")
                                box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                                box.prop(shader_node.inputs[3], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")

                            elif shader_node.name.startswith("BagaPie_V2"):
                                if "Bark" in shader_node.label:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    idx_input = 4
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 5
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 11
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                    idx_input = 12
                                    box.prop(shader_node.inputs[idx_input], 'default_value', text = shader_node.inputs[idx_input].name)
                                else:
                                    box = layout.box()
                                    box.label(text= (m.name[:-4]).removeprefix('BagaPie_V2_'))
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                    box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                    box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                    box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                    box.separator(factor = 0.5)
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                    box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                    if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                        box.label(text="Season value up to 0.9", icon = 'ERROR')
                                        box.label(text="This value add transparency.")
                                        box.label(text="May increase render time !")
                                        box.label(text="Decrease Season or Random Season")
                                    box.separator(factor = 0.5)
                                    box = box.column(align=True)
                                    box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                    box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                    box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")
                                    box.prop(shader_node.inputs[12], 'default_value', text = "Disable Alpha")

                            else:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[1], 'default_value', text = "Brightness")
                                box.prop(shader_node.inputs[2], 'default_value', text = "Random Brightness")
                                box.prop(shader_node.inputs[3], 'default_value', text = "Saturation")
                                box.prop(shader_node.inputs[4], 'default_value', text = "Random Saturation")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[5], 'default_value', text = "Season")
                                box.prop(shader_node.inputs[6], 'default_value', text = "Random Season")
                                if shader_node.inputs[5].default_value + (shader_node.inputs[6].default_value) >= 0.9:
                                    box.label(text="Season value up to 0.9", icon = 'ERROR')
                                    box.label(text="This value add transparency.")
                                    box.label(text="May increase render time !")
                                    box.label(text="Decrease Season or Random Season")
                                box.separator(factor = 0.5)
                                box = box.column(align=True)
                                box.prop(shader_node.inputs[7], 'default_value', text = "Translucent")
                                box.prop(shader_node.inputs[10], 'default_value', text = "Specular")
                                box.prop(shader_node.inputs[11], 'default_value', text = "Roughness")

                elif mo_type == "stump":
                    material_slots = obj.material_slots
                    for m in material_slots:
                        material = m.material
                        nodes = material.node_tree.nodes
                        for node in nodes:
                            if node.name == modifiers[0]:
                                shader_node = node
                        
                        if shader_node.name.startswith("BagaPie_V2"):
                            if "Wood" in shader_node.name:
                                box = layout.box()
                                box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                                box = box.column(align=True)
                                inp = shader_node.inputs

                                idx_input = [10,11,12,13]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.separator(factor = 0.5)
                                box.prop(shader_node.inputs[14], 'default_value', text = "Tint")
                                box.prop(shader_node.inputs[15], 'default_value', text = "")
                                box.separator(factor = 0.5)
                                idx_input = [4,5]
                                for i in idx_input:
                                    box.prop(inp[i], 'default_value', text = inp[i].name)
                                box.label(text="Bump")
                                box.prop(shader_node.inputs[7], 'default_value', text = "Threshold")
                                box.prop(shader_node.inputs[8], 'default_value', text = "Intensity")
                                box.label(text="Ambient Occlusion")
                                box.prop(shader_node.inputs[6], 'default_value', text = "AO (Map)")
                                if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
                                    if not bpy.context.scene.eevee.use_gtao:
                                        box.label(text="AO disabled")
                                        box.prop(bpy.context.scene.eevee, 'use_gtao', text = "Use AO")
                                box.prop(shader_node.inputs[16], 'default_value', text = "AO Intensity")
                                box.prop(shader_node.inputs[17], 'default_value', text = "AO Distance")
                                
                    if shader_node.name.startswith("BagaPie_V2"): 
                        pass
                    elif shader_node.name.startswith("BagaPie_PL_Tree_Trunk"):
                        box = layout.box()
                        box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                        box = box.column(align=True)
                        box.prop(shader_node.inputs[0], 'default_value', text = "AO")
                        box.prop(shader_node.inputs[1], 'default_value', text = "AO Distance")
                        box.prop(shader_node.inputs[8], 'default_value', text = "AO Tint")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[2], 'default_value', text = "Tint Intensity")
                        box.prop(shader_node.inputs[3], 'default_value', text = "")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[5], 'default_value', text = "Brightness")
                        box.prop(shader_node.inputs[4], 'default_value', text = "Saturation")
                    else:
                        col.label(text="Stump Shader :")
                        box = layout.box()
                        box.label(text= (m.name[:-4]).removeprefix('BagaPie_'))
                        box = box.column(align=True)
                        box.prop(shader_node.inputs[1], 'default_value', text = "Saturation")
                        box.prop(shader_node.inputs[2], 'default_value', text = "Random Saturation")
                        box.prop(shader_node.inputs[3], 'default_value', text = "Brightness")
                        box.prop(shader_node.inputs[4], 'default_value', text = "Random Brightness")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[6], 'default_value', text = "Tint")
                        box.prop(shader_node.inputs[5], 'default_value', text = "")
                        box.separator(factor = 0.5)
                        box.prop(shader_node.inputs[7], 'default_value', text = "Specular")
                        box.prop(shader_node.inputs[8], 'default_value', text = "Roughness")

                        box.label(text="Bump")
                        box.prop(shader_node.inputs[12], 'default_value', text = "Threshold")
                        box.prop(shader_node.inputs[13], 'default_value', text = "Intensity")
                        box.label(text="Ambient Occlusion")
                        box.prop(shader_node.inputs[14], 'default_value', text = "Intensity")
                        box.prop(shader_node.inputs[15], 'default_value', text = "Distance")

                elif mo_type == "instancesdisplace":
                    modifier_header_basic(col)
                    psi_modifier = obj.modifiers[modifiers[0]]

                    col = layout.column(align=True)
                    box = layout.box()
                    box.label(text="Noise Texture")
                    box = box.column(align=True)
                    box.prop(psi_modifier, '["Input_3"]', text = "Scale")
                    box.prop(psi_modifier, '["Input_4"]', text = "Noise")
                    box = layout.box()
                    box.label(text="Intensity XYZ")
                    row = box.row(align=True)
                    row.prop(psi_modifier, '["Input_2"]', text = "")
                    box.label(text="Noise Position XYZ")
                    row = box.row(align=True)
                    row.prop(psi_modifier, '["Input_5"]', text = "")

                elif mo_type == "paving":
                    modifier_header_basic(layout)
                    modifier = obj.modifiers[modifiers[0]]

                    # MAIN PARAMETERS
                    box = layout.box()
                    box.label(text="Main Parameters", icon="MODIFIER")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_2"]', text="Sharp Threshold")
                    col.prop(modifier, '["Socket_3"]', text="Rotation")
                    col.prop(modifier, '["Socket_4"]', text="Length")
                    col.prop(modifier, '["Socket_5"]', text="Width")
                    col.prop(modifier, '["Socket_6"]', text="Width Offset")
                    col.prop(modifier, '["Socket_7"]', text="Length Offset")
                    col.prop(modifier, '["Socket_8"]', text="Width Scale")
                    col.prop(modifier, '["Socket_9"]', text="Length Scale")

                    # BORDER PROPERTIES
                    box = layout.box()
                    box.label(text="Border Properties", icon="CURVE_DATA")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_10"]', text="Resample Border")
                    col.prop(modifier, '["Socket_11"]', text="Length Herringbone Warp")
                    col.prop(modifier, '["Socket_12"]', text="Width Herringbone Warp")

                    # RANDOMIZATION
                    box = layout.box()
                    box.label(text="Randomization", icon="RNDCURVE")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_13"]', text="Random Deform")
                    col.prop(modifier, '["Socket_17"]', text="Random Thickness")
                    col.prop(modifier, '["Socket_27"]', text="Seed")

                    # TILES
                    box = layout.box()
                    box.label(text="Tile Properties", icon="TEXTURE")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_14"]', text="Insert Tiles")
                    col.prop(modifier, '["Socket_15"]', text="Taper")
                    col.prop(modifier, '["Socket_16"]', text="Thickness")

                    # EDGING
                    input_index = "Socket_24"
                    box = layout.box()
                    box.scale_y = 2 if not modifier[input_index] else 1
                    props = box.operator('switch.button', text='Edging', depress=modifier[input_index])
                    props.index = input_index

                    if modifier[input_index]:
                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_19"]', text="Edging Scale")
                        col.prop(modifier, '["Socket_20"]', text="Edging Taper")
                        col.prop(modifier, '["Socket_21"]', text="Edging Width")
                        col.prop(modifier, '["Socket_22"]', text="Edging Thickness")
                        col.prop(modifier, '["Socket_23"]', text="Edging Random Thickness")

                    # POSITION OFFSET
                    box = layout.box()
                    box.label(text="Position Offset", icon="PIVOT_BOUNDBOX")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_25"]', text="Offset X")
                    col.prop(modifier, '["Socket_26"]', text="Offset Y")

                    # SURFACE
                    box = layout.box()
                    box.label(text="Surface Deformation", icon="MOD_DISPLACE")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_18"]', text="Surface Deform")

                    layout.prop_search(modifier, '["Socket_28"]', bpy.data, "materials", text="Material", icon="MATERIAL"),

                elif mo_type == "grid":
                    modifier_header_basic(layout)
                    modifier = obj.modifiers[modifiers[0]]

                    # MAIN PARAMETERS
                    box = layout.box()
                    box.label(text="Main Parameters", icon="MODIFIER")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_2"]', text="Sharp Threshold")
                    col.prop(modifier, '["Socket_3"]', text="Rotation")
                    col.prop(modifier, '["Socket_5"]', text="Distance X")
                    col.prop(modifier, '["Socket_4"]', text="Distance Y")

                    # GRID PROPERTIES
                    box = layout.box()
                    box.label(text="Grid Properties", icon="GRID")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_30"]', text="Offset Grid")
                    col.prop(modifier, '["Socket_31"]', text="Offset X")
                    col.prop(modifier, '["Socket_32"]', text="Offset Y")

                    # PROFIL SETTINGS
                    box = layout.box()
                    box.label(text="Profil")
                    row = box.row(align=True)
                    row.scale_y = 1.5
                    row.operator('switch.button', text='Circle', depress=modifier["Socket_26"]).index = "Socket_26"
                    row.operator('switch.button', text='Quad', depress=not modifier["Socket_26"]).index = "Socket_26"
                        
                    if modifier['Socket_26']:
                        box.prop(modifier, '["Socket_25"]', text="Radius")
                        box.prop(modifier, '["Socket_27"]', text="Resolution")
                    else:
                        box.prop(modifier, '["Socket_28"]', text="Width")
                        box.prop(modifier, '["Socket_29"]', text="Height")

                    box.prop(modifier, '["Socket_34"]', text="Fix Tilt (Parallelogram)")

                    layout.prop_search(modifier, '["Socket_33"]', bpy.data, "materials", text="Material", icon="MATERIAL"),

                elif mo_type == "perforated_grid":
                    modifier_header_basic(layout)
                    modifier = obj.modifiers[modifiers[0]]

                    # MAIN PARAMETERS
                    box = layout.box()
                    box.label(text="Main Parameters", icon="MODIFIER")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_2"]', text="Sharp Threshold")
                    col.prop(modifier, '["Socket_3"]', text="Rotation")
                    col.prop(modifier, '["Socket_4"]', text="Length")
                    col.prop(modifier, '["Socket_5"]', text="Width")

                    # OFFSET SETTINGS
                    box = layout.box()
                    box.label(text="Offset Settings", icon="GRID")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_6"]', text="Width Offset")
                    col.prop(modifier, '["Socket_7"]', text="Length Offset")
                    col.prop(modifier, '["Socket_29"]', text="Hole Offset")
                    col.prop(modifier, '["Socket_26"]', text="Offset X")
                    col.prop(modifier, '["Socket_27"]', text="Offset Y")

                    # HERRINGBONE WARP ###### BROKEN : Need to fix the Node Tree !!! T_T
                    # box = layout.box()
                    # box.label(text="Herringbone Warp", icon="CURVE_DATA")

                    # col = box.column(align=True)
                    # col.prop(modifier, '["Socket_11"]', text="Length Herringbone Warp")
                    # col.prop(modifier, '["Socket_12"]', text="Width Herringbone Warp")

                    # SCALE SETTINGS
                    box = layout.box()
                    box.label(text="Scale Settings", icon="ARROW_LEFTRIGHT")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_24"]', text="Length Scale")
                    col.prop(modifier, '["Socket_25"]', text="Width Scale")

                    # THICKNESS SETTINGS
                    box = layout.box()
                    box.label(text="Thickness Settings", icon="MOD_SOLIDIFY")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_16"]', text="Thickness")
                    col.prop(modifier, '["Socket_17"]', text="Random Thickness")

                    # RANDOMIZATION
                    box = layout.box()
                    box.label(text="Randomization", icon="RNDCURVE")

                    col = box.column(align=True)
                    col.prop(modifier, '["Socket_28"]', text="Seed")

                    layout.prop_search(modifier, '["Socket_30"]', bpy.data, "materials", text="Material", icon="MATERIAL"),

                elif mo_type == "plank":
                    if modifiers[0] not in obj.modifiers:
                        layout.label(text="Modifier is missing", icon='ERROR')
                        layout.label(text="If present, rename it :")
                        layout.label(text=modifiers[0])
                    else:
                        modifier_header_basic(layout)
                        modifier = obj.modifiers[modifiers[0]]

                        # MAIN PARAMETERS
                        box = layout.box()
                        box.label(text="Main Parameters", icon="MODIFIER")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_4"]', text="Length")
                        col.prop(modifier, '["Socket_5"]', text="Width")
                        col.prop(modifier, '["Socket_3"]', text="Rotation")
                        col.prop(modifier, '["Socket_2"]', text="Sharp Threshold (Cut)")

                        # OFFSET SETTINGS
                        box = layout.box()
                        box.label(text="Offset Settings", icon="GRID")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_7"]', text="Length Offset")
                        col.prop(modifier, '["Socket_26"]', text="Offset X")
                        col.prop(modifier, '["Socket_27"]', text="Offset Y")

                        # SCALE SETTINGS
                        box = layout.box()
                        box.label(text="Scale Settings", icon="ARROW_LEFTRIGHT")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_8"]', text="Width Scale")
                        col.prop(modifier, '["Socket_9"]', text="Length Scale")

                        # THICKNESS SETTINGS
                        box = layout.box()
                        box.label(text="Thickness Settings", icon="MOD_SOLIDIFY")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_16"]', text="Thickness")
                        col.prop(modifier, '["Socket_17"]', text="Random Thickness")
                        col.prop(modifier, '["Socket_25"]', text="Tile Skew")

                        # RANDOMIZATION
                        box = layout.box()
                        box.label(text="Randomization", icon="RNDCURVE")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_13"]', text="Random Deform")
                        col.prop(modifier, '["Socket_31"]', text="Random Rotate Y")
                        col.prop(modifier, '["Socket_32"]', text="Random Rotate X")
                        col.prop(modifier, '["Socket_18"]', text="Surface Deform")
                        col.prop(modifier, '["Socket_30"]', text="Random Offset")
                        col.prop(modifier, '["Socket_29"]', text="Seed")

                        # DELETION SETTINGS
                        box = layout.box()
                        box.label(text="Debug", icon="X")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_28"]', text="Delete Small Area")

                        layout.prop_search(modifier, '["Socket_33"]', bpy.data, "materials", text="Material", icon="MATERIAL"),

                elif mo_type == "array_along_shape":
                    if modifiers[0] not in obj.modifiers:
                        layout.label(text="Modifier is missing", icon='ERROR')
                        layout.label(text="If present, rename it :")
                        layout.label(text=modifiers[0])
                    else:
                        modifier_header_basic(layout)
                        modifier = obj.modifiers[modifiers[0]]

                        # MAIN PARAMETERS
                        box = layout.box()
                        box.label(text="Main Parameters", icon="MODIFIER")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_12"]', text="Count")
                        col.prop(modifier, '["Socket_2"]', text="Precision")
                        col.prop(modifier, '["Socket_10"]', text="Distance")
                        box.label(text="Array might fail on sharp edges (>70°)")

                        # RANDOMIZATION
                        box = layout.box()
                        box.label(text="Randomization", icon="RNDCURVE")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_3"]', text="Position")
                        col.prop(modifier, '["Socket_4"]', text="Rotation X")
                        col.prop(modifier, '["Socket_5"]', text="Rotation Y")
                        col.prop(modifier, '["Socket_6"]', text="Rotation Normal")
                        col.prop(modifier, '["Socket_7"]', text="Scale Min")
                        col.prop(modifier, '["Socket_8"]', text="Scale Max")
                        col.prop(modifier, '["Socket_14"]', text="Seed")

                        # ORIENTATION SETTINGS
                        box = layout.box()
                        box.label(text="Orientation Settings", icon="ORIENTATION_GIMBAL")

                        col = box.column(align=True)
                        col.prop(modifier, '["Socket_9"]', text="Orientation Angle")
                        col.prop(modifier, '["Socket_13"]', text="Smooth Rotation")
                        
                        box.label(text="Lock Axis :")
                        row = box.row(align=True)
                        row.prop(modifier, '["Socket_17"]', text="X", toggle=True, icon='LOCKED' if modifier["Socket_17"] else 'UNLOCKED')
                        row.prop(modifier, '["Socket_18"]', text="Y", toggle=True, icon='LOCKED' if modifier["Socket_18"] else 'UNLOCKED')
                        row.prop(modifier, '["Socket_19"]', text="Z", toggle=True, icon='LOCKED' if modifier["Socket_19"] else 'UNLOCKED')

                        box.label(text="TIPS : Don't use Rot Ang and Lock Axis together")

                        # COLLECTION SETTINGS
                        box = layout.box()
                        box.label(text="Target", icon="OUTLINER_COLLECTION")

                        col = box.column(align=True)
                        col.prop_search(modifier, '["Socket_16"]', bpy.data, "collections", text="", icon="OUTLINER_COLLECTION")

                else:
                    displaydoc == True

            #################################################################################
            # GROUP
            #################################################################################
            elif obj and obj.get("bagapie") == "bound_box":

                layout.label(text="Group :")
                box = layout.box()

                found_gp_sh = any(
                    kmi.idname == "bagapie.group"
                    for km, _ in keyconfig_merge(context.window_manager.keyconfigs.user, context.window_manager.keyconfigs.user)
                    for kmi in km.keymap_items
                )
                if found_gp_sh:
                    row = box.row(align=True)
                    row.split(factor=0.5)
                    row.label(text="Group Objects :")
                    row.label(text="Ctrl + G")
                else:
                    box.operator('bagapie.replace_shortcut', text="Add Group Shortcut")

                row = box.row(align=True)
                row.split(factor=0.5)
                row.label(text="Duplicate :")
                row.label(text="Alt + J")
                row = box.row(align=True)
                row.split(factor=0.5)
                row.label(text="Duplicate Linked :")
                row.label(text="Alt + N")

                col = layout.column()
                col.scale_y = 1.2

                row = col.row(align=True)
                split = row.split(factor=0.85, align=True)
                if obj["bagapie_locker"] == True:
                    split.operator("bagapie.editgroup", text="Make Content Selectable", icon ="RESTRICT_SELECT_OFF")
                    split.operator("bagapie.editgroup", text="All").all = True
                else:
                    split.operator("bagapie.lockgroup", text="Make Content Unlectable",icon="RESTRICT_SELECT_ON")
                    split.operator("bagapie.lockgroup", text="All").all = True
                col.operator("bagapie.instance", text= "Group to Instance", icon="LINKED")

                if is_in_local_view():
                    col.operator("bagapie.isolategroup", text= "Unisolate", icon="ZOOM_PREVIOUS")
                else:
                    col.operator("bagapie.isolategroup", text= "Isolate", icon="ZOOM_PREVIOUS")

                col.operator("bagapie.ungroup", text= "Ungroup", icon="MOD_EXPLODE")
                col.operator("bagapie.deletegroup", text= "Delete Group (ALL)", icon="TRASH")

                col.label(text="Group Content:")
                row = col.row(align=True)
                row.operator("bagapie.addgroup", text= "Add", icon="ADD")
                row.operator("bagapie.removegroup", text= "Remove", icon="REMOVE")

                row = col.row(align=True)
                row.operator("bagapie.moveonlygroup", text= "Link Obj to Group Coll Only", icon="OUTLINER_COLLECTION")
                tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                tips.message = "Objects in the selected group may be linked to multiple collections in your scene. This tool will remove them from all collections except the group's collection. If these objects are needed in other collections, avoid using this tool."

                if check_parent_group(obj):
                    col.operator("bagapie.move_group_modal", text= "Move Instance Group", icon="EMPTY_ARROWS").is_parent = True

                if bagapie_pref.feature_enabled == False:
                    row = col.row(align=True)
                    row.operator("bagapie.double_click_edit", text="Double Clic Edit - OFF", icon ="MOUSE_LMB")
                    tips = row.operator("bagapie.tooltips", text="", depress = False, icon = 'INFO')
                    tips.message = "Beta Feature : When double clicking on an instance or a group, it will isolate it. Double click to go back."
                else:
                    col.label(text="Double Clic Edit - ON", icon='CHECKBOX_HLT')

                displaydoc=False

            elif obj.parent and obj.parent.get("bagapie") and obj.parent["bagapie"] == "bound_box" or any(col.name.startswith("BagaPie_Group") for col in obj.users_collection):
                if check_group_instance(obj) == True:
                    col = layout.column()
                    col.scale_y = 2
                    col.operator("bagapie.move_group_modal", text= "Move Instance Group", icon="EMPTY_ARROWS").is_parent = False
                    displaydoc=False
                    
            elif obj is not None and obj.type == 'EMPTY' and any(coll.name == "BagaPie_Instances" for coll in obj.users_collection):
                if is_in_local_view()==False:
                    col = layout.column()
                    col.scale_y = 2
                    col.operator("bagapie.editinstancegroup", text= "Edit Instance Group", icon="GREASEPENCIL")

            row_tuto = layout.row(align=True)
            row_tuto.scale_y = 1.3
            row_tuto.operator("wm.url_open", text="Tutorials Playlist !", icon = 'PLAY').url = "https://youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu&si=Y4MRQn_aTIQUXOpw"
            row_tuto.operator("wm.url_open", text="", icon = 'TEXT').url = "https://www.f12studio.fr/bagapiev6"


        # In case nothing is selected ...
        elif obj and obj.type not in obj_allowed_types:
            box = layout.box()
            box = box.column(align=True)
            box.label(text="This object is not supported")
            box.label(text="Mesh or Curve Only")

        else:
            displaydoc=True

        if is_in_local_view()==True:
            col = layout.column()
            col.scale_y = 2
            col.operator("view3d.localview", text= "Exit Editing", icon="LOOP_BACK")


        #################################################################################
        # NODES TO PANEL
        #################################################################################

        # DISPLAY MODIFIER AND MATERIAL
            # "Node to Panel" allow to create cusrom N panels for modifier and shaders in the BagaPie tab :
            #  - For geometry nodes tree : Set the "BP_" prefix in the name, description of you node tree. This prefix informs Bagapie to display your node tree.
            #  - For materials : Only for NodeGroups; Set the "BP_" prefix in the node group name or in the node name/label.
            #  - Then, to display node group inputs, set a prefix (eg V_) in the input name/description.

        if obj is not None:
            buttons_display = []
            check_BP_ = "BP_"

            if obj.type == 'MESH' or 'CURVE':

                check_URL_ = "URL_"
                check_L_ = "L_"
                check_C_ = "C_"
                check_S_ = "S_"
                check_V_ = "V_"
                check_P = "P"
                check_P_ = "P_"
                check_B = "B"
                check_R = "R"
                check_ = "_"
                layout_recur = layout
                lay_list = {}

                # DISPLAY MODIFIER
                for mo in obj.modifiers:
                    if mo.type == "NODES" and mo is not None and mo.node_group is not None:

                        # DISPLAY MODIFIER PANEL
                        if  mo.name.startswith("BP_") or mo.node_group.name.startswith("BP_") or mo.node_group.description.startswith("BP_"):
                            displaydoc = False
                            row_head = layout.row(align=True)
                            row_headception = row_head.row(align=True)
                            row_headception.alignment  = 'LEFT'
                            row_headception.prop(mo, 'show_expanded', text="", emboss=False)
                            row_headception.prop(mo, 'show_expanded', text=mo.node_group.name, icon = 'GEOMETRY_NODES', emboss=False)
                            row_headception2 = row_head.row(align=True)
                            row_headception2.alignment  = 'RIGHT'
                            row_headception2.prop(mo, 'show_on_cage', text="")
                            row_headception2.prop(mo, 'show_in_editmode', text="")
                            row_headception2.prop(mo, 'show_viewport', text="")
                            row_headception2.prop(mo, 'show_render', text="")
                            if mo.show_expanded == False:
                                continue

                            for input in mo.node_group.interface.items_tree:
                                Nodes_to_Panel_Geometry_Nodes(input,mo,layout,buttons_display,lay_list,layout_recur)
                        
                    
                        # DISPLAY NODES GROUPS SUBPANELS
                        for node in mo.node_group.nodes:
                            if node.type == 'GROUP':
                                if node.node_tree.description.startswith(check_BP_) or node.node_tree.name.startswith(check_BP_) or node.name.startswith(check_BP_) or node.label.startswith(check_BP_):
                                    box=layout.box()
                                    row_head = box.row(align=True)
                                    row_head.alignment  = 'LEFT'
                                    row_head.prop(node, 'hide', text="", icon = 'RIGHTARROW' if node.hide else 'DOWNARROW_HLT', emboss=False)
                                    if node.label != "":
                                        name = node.label
                                    else:
                                        name = node.node_tree.name
                                    row_head.prop(node, 'hide', text=name, emboss=False)
                                    if node.hide:
                                        continue
                                    for input in node.inputs:
                                        if input != node.inputs[0]:
                                            Nodes_to_Panel_Geometry_Nodes(input,node,box,buttons_display,lay_list,layout_recur,input_id="default_value")


                        if mo.is_active:
                            layout.operator("bagapie.geopack_create_modifier", text = "Save as GeoPack Modifier")

                # DISPLAY MATERIAL
                for mat in obj.material_slots:
                    if mat.material: #if a material is assign to the slot
                        material = bpy.data.materials[mat.name]
                        for node in material.node_tree.nodes:
                            if node.type == 'GROUP':
                                if node.node_tree.description.startswith(check_BP_) or node.node_tree.name.startswith(check_BP_) or node.name.startswith(check_BP_) or node.label.startswith(check_BP_):
                                    displaydoc = False
                                    mat_name = node.node_tree.name.removeprefix('BP_')
                                    if node.label != "":
                                        mat_name=node.label.removeprefix('BP_')
                                    row_head = layout.row(align=True)
                                    row_head.alignment  = 'LEFT'
                                    row_head.prop(node, 'hide', text="", icon = 'RIGHTARROW' if node.hide else 'DOWNARROW_HLT', emboss=False)
                                    row_head.prop(node, 'hide', text=mat_name, icon='MATERIAL', emboss=False)
                                    if node.hide:
                                        continue

                                    for input in node.inputs:
                                        id = input.name
                                        idd = node.node_tree.interface.items_tree[input.name].description

                                        checks = ["URL_", "L_", "C_", "S_", "V_", "P", "P_", "B", "B_", "R", "R_", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
                                        for c in checks:
                                            if idd.startswith(c):
                                                if id.startswith(("B", "R")):
                                                    id = " "+input.name
                                                id = idd + id
                                                break
                                        
                                        Material_Input_Type(id, idd, input, check_L_, check_S_, check_V_, layout)
                                            
                                        check_B = "B"
                                        check_R = "R"
                                        if id.startswith(check_B) or idd.startswith(check_B) or id.startswith(check_R) or idd.startswith(check_R):
                                            id_final, idd_final, layout_final = Recustive_ui(id, idd, layout_recur, layout, lay_list, "")
                                            Material_Input_Type(id_final, idd_final, input, check_L_, check_S_, check_V_, layout_final)
                                            layout_recur = layout_final

            if obj.name.startswith("Ivy_Parent"):
                box = layout.box()
                box.scale_y = 2
                box.operator("bagapie.removesingleivy", text= "Delete this part of ivy")

        # DISPLAY DOC AND YOUTUBE TUTORIAL
        if displaydoc == True and is_in_local_view() == False:
            box = layout.box()
            box.scale_y = 0.5
            
            row = box.row(align=True)
            split = row.split(factor=0.7)
            split.label(text="Menu :")
            split.label(text="Key :")

            box.separator(factor = 0.5)

            wm = bpy.context.window_manager
            kc_user = wm.keyconfigs.user
            display_keymaps = kc_user.keymaps

            found_gp_sh = False
            for km in display_keymaps:
                for kmi in km.keymap_items:
                    if kmi.idname == "bagapie.group":
                        found_gp_sh = True
                        break
                if found_gp_sh:
                    break
            
            for km in display_keymaps:
                for kmi in km.keymap_items:
                    # PIE MENU MAIN
                    if kmi.name == 'BagaPie':
                        shortcut = format_shortcut(kmi)
                        row = box.row(align=True)
                        split = row.split(factor=0.7)
                        split.label(text="Main Pie (Object Mode)")
                        split.label(text=shortcut)

                    # PIE MENU TOOLS
                    if kmi.name == 'BagaPie Tools':
                        shortcut = format_shortcut(kmi)
                        row = box.row(align=True)
                        split = row.split(factor=0.7)
                        split.label(text="Tools Pie (Edit Mode)")
                        split.label(text=shortcut)

                    # GEOPACK
                    if kmi.name == 'BagaPie GeoPack':
                        shortcut = format_shortcut(kmi)
                        row = box.row(align=True)
                        split = row.split(factor=0.7)
                        split.label(text="GeoPack")
                        split.label(text=shortcut)

                    # GROUP SHORTCUT
                    if kmi.idname == "bagapie.group" and found_gp_sh == True:
                        row = box.row(align=True)
                        split = row.split(factor=0.7)
                        split.label(text="Group") 
                        shortcut = format_shortcut(kmi)
                        split.label(text=shortcut)
                    elif found_gp_sh == False:
                        row = box.row(align=True)
                        split = row.split(factor=0.7)
                        split.label(text="Group") 
                        split.operator('bagapie.replace_shortcut', text="+")
                        found_gp_sh = True


###################################################################################
# NODE TO PANEL UTILS
###################################################################################
def Dispay_Value(input, col, mo, input_id, id):
    if input == mo:
        col.prop(mo, input_id, text=id)
    elif input.bl_socket_idname == 'NodeSocketMaterial':
        col.prop_search(mo, input_id, bpy.data, "materials", text=id, icon="MATERIAL"), 
    elif input.bl_socket_idname == 'NodeSocketObject':
        col.prop_search(mo, input_id, bpy.data, "objects", text=id, icon="OBJECT_DATA"), 
    elif input.bl_socket_idname == 'NodeSocketCollection':
        col.prop_search(mo, input_id, bpy.data, "collections", text=id, icon="OUTLINER_COLLECTION"), 
    elif input.bl_socket_idname == 'NodeSocketImage':
        col.prop_search(mo, input_id, bpy.data, "images", text=id, icon="IMAGE"), 
    else:
        col.prop(mo, input_id, text=id)

def Format_Id(id, check, layout):
    id = id.removeprefix(check)
    col = layout.column()
    if id[0].isdigit() and id[1] == "_":
        col.scale_y = int(id[0])
        id = id.removeprefix(str(id[0])+"_")
    return id, col

def Display_Curve(mo, id, col):
    found=False
    for node in mo.node_group.nodes:
        if node.name.endswith(id) or node.label.endswith(id):
            if node.type == 'VALTORGB':
                col.template_color_ramp(node, "color_ramp")
                found=True
                break
            elif node.type == 'CURVE_FLOAT':
                col.template_curve_mapping(node, "mapping")
                found=True
                break
    if not found:
        box=col.box()
        box.scale_y=0.6
        box.label(text="'"+id +"' Node not found")
        box.label(text="Node and Input must have the same name")

def Display_Button(input, mo, col, id):
    input_index = input.identifier
    if mo[input_index] == gn_bool_version(1):
        props = col.operator('switch.boolcustom', text=id, depress = True)
    else:
        props = col.operator('switch.boolcustom', text=id, depress = False)
    props.index = input_index
    props.modifier = mo.name

def Display_URL(mo, input, col, id):
    url_link = mo[input.identifier]
    if url_link == "":
        url_link = input.default_value
    if input.socket_type == "NodeSocketString" and url_link != "":
        col.operator("wm.url_open", text=id, icon = 'URL').url = url_link
    elif input.socket_type != "NodeSocketString":
        col.label(text="'"+id+"' input must be String type", icon = 'URL')
    else:
        col.label(text="'"+id+"': Set URL as input default value", icon = 'URL')

def Material_Input_Type(id, idd, input, check_L_, check_S_, check_V_, layout):
    if id.startswith(check_L_) or idd.startswith(check_L_):
        id, col = Format_Id(id, check_L_, layout)
        col.label(text=id)

    elif id.startswith(check_S_) or idd.startswith(check_S_):
        id = id.removeprefix(check_S_)
        layout.separator(factor = int(id[0]))

    elif id.startswith(check_V_) or idd.startswith(check_V_):
        id, col = Format_Id(id, check_V_, layout)
        col.prop(input, "default_value", text=id)

def GeoNode_Input_Type(id, idd, input, mo, input_id, check_L_, check_S_, check_V_, check_C_, check_P_, check_URL_, layout):
    if id.startswith(check_L_) or idd.startswith(check_L_):
        id, col = Format_Id(id, check_L_, layout)
        col.label(text=id)

    elif id.startswith(check_S_) or idd.startswith(check_S_):
        id = id.removeprefix(check_S_)
        layout.separator(factor = int(id[0]))

    elif id.startswith(check_V_) or idd.startswith(check_V_):
        id, col = Format_Id(id, check_V_, layout)
        Dispay_Value(input, col, mo, input_id, id)

    elif id.startswith(check_C_) or idd.startswith(check_C_):
        id, col = Format_Id(id, check_C_, layout)
        Display_Curve(mo, id, col)

    elif id.startswith(check_P_) or idd.startswith(check_P_) and input.bl_socket_idname == 'NodeSocketBool':
        id, col = Format_Id(id, check_P_, layout)
        Display_Button(input, mo, col, id)

    elif id.startswith(check_URL_) or idd.startswith(check_URL_):
        id, col = Format_Id(id, check_URL_, layout)
        Display_URL(mo, input, col, id)

def Display_All(id, idd, mo, input, input_id, layout):
    check_URL_ = "URL_"
    check_L_ = "L_"
    check_C_ = "C_"
    check_S_ = "S_"
    check_V_ = "V_"

    if id.startswith(check_URL_) or idd.startswith(check_URL_):
        id, col = Format_Id(id, check_URL_, layout)
        Display_URL(mo, input, col, id)
        return True
        
    elif id.startswith(check_L_) or idd.startswith(check_L_):
        id, col = Format_Id(id, check_L_, layout)
        col.label(text=id)
        return True

    elif id.startswith(check_C_) or idd.startswith(check_C_):
        id, col = Format_Id(id, check_C_, layout)
        Display_Curve(mo, id, col)
        return True

    elif id.startswith(check_S_) or idd.startswith(check_S_):
        id = id.removeprefix(check_S_)
        layout.separator(factor = int(id[0]))
        return True

    elif id.startswith(check_V_) or idd.startswith(check_V_):
        id, col = Format_Id(id, check_V_, layout)
        Dispay_Value(input, col, mo, input_id, id)
        return True
    return False

def remove_prefix(id, idd, check_X):
    id = id.removeprefix(check_X)
    idd = idd.removeprefix(check_X)
    return id, idd

def Recustive_ui(id, idd, layout_recur, layout, lay_list, id_name):
    layout_temp = layout_recur

    for prefix, suffix in [("B", "B"), ("R", "R")]:
        if (id.startswith(prefix) or idd.startswith(prefix)) and "_" in id:
            layout = lay_list.get(id_name, layout)
            id_name += suffix
            id, idd = remove_prefix(id, idd, prefix)

            if id.startswith("_") or idd.startswith("_"):
                id, idd = remove_prefix(id, idd, "_")

                if prefix == "B":
                    layout_recur = layout.box().column(align=True)
                elif prefix == "R":
                    layout_recur = layout.row(align=True)

                layout = layout_recur
                lay_list[id_name] = layout_recur
            else:
                layout = layout_temp

            return Recustive_ui(id, idd, layout_recur, layout, lay_list, id_name)

    if lay_list.get(id_name) is not None:
        layout_recur = lay_list[id_name]

    return id, idd, layout_recur

def Recursive_call(check_B,id,idd,check_R,mo,input_id,input,layout,lay_list,layout_recur):
    if id.startswith(check_B) or idd.startswith(check_B) or id.startswith(check_R) or idd.startswith(check_R):
        id_final, idd_final, layout_final = Recustive_ui(id, idd, layout_recur, layout, lay_list, "")
        Display_All(id_final, idd_final, mo, input, input_id, layout_final)
        layout_recur = layout_final

def Nodes_to_Panel_Geometry_Nodes(input,mo,layout,buttons_display,lay_list,layout_recur,input_id="NONE"):
    check_URL_ = "URL_"
    check_L_ = "L_"
    check_C_ = "C_"
    check_S_ = "S_"
    check_V_ = "V_"
    check_P = "P"
    check_P_ = "P_"
    check_B = "B"
    check_R = "R"
    check_ = "_"
    
    if input_id == "NONE":
        id = input.name
        idd = input.description
    else:
        identifier = input.identifier
        inputs = list(mo.node_tree.interface.items_tree.values())
        index = next((i for i, item in enumerate(inputs) if item.identifier == identifier), -1)
        id = mo.node_tree.interface.items_tree[index].name
        idd = mo.node_tree.interface.items_tree[index].description
        mo=input


    checks = ["URL_", "L_", "C_", "S_", "V_", "P", "P_", "B", "B_", "R", "R_", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    for c in checks: # This loop properly combine the input name and description
        if idd.startswith(c):
            if id.startswith(("B", "R")):
                id = " "+input.name
            desc=idd
            checks_desc = checks[:]
            checks_desc.append("_") 
            while any(desc.startswith(prefix) for prefix in checks_desc):
                for prefix in checks_desc:
                    if desc.startswith(prefix):
                        desc = desc.removeprefix(prefix)
            idd = idd[:len(idd) - len(desc)]
            id = idd + id
            break
    if input_id == "NONE":
        input_id = '["{}"]'.format(bpy.utils.escape_identifier(input.identifier))
    

    # Display_All => Draw values, labels, URL, curves, separators
    if Display_All(id, idd, mo, input, input_id, layout) == False:

        # BUTTONS
        if id.startswith(check_P) or idd.startswith(check_P) and input.bl_socket_idname == 'NodeSocketBool':
            id = id.removeprefix(check_P)
            
            if id.startswith(check_) or idd.startswith(check_):
                id, col = Format_Id(id, check_, layout)
                Display_Button(input, mo, col, id)

            elif id[0].isdigit() and id[1] == '_':
                buttons_display.append([id[0], mo[input.identifier]])

                id = id[2:]
                col = layout.column()
                if id[0].isdigit() and id[1] == "_":
                    col.scale_y = int(id[0])
                    id = id.removeprefix(str(id[0])+"_")
                    
                Display_Button(input, mo, col, id)
        
        # BUTTONS CHILDREN
        elif id[0].isdigit():
            button_id = id[0]
            id = id.removeprefix(id[0])
            display_line = False

            for button in buttons_display:
                if button_id in button[0] and button[1]:
                    display_line = True

            if display_line:
                GeoNode_Input_Type(id, idd, input, mo, input_id, check_L_, check_S_, check_V_, check_C_, check_P_, check_URL_, layout)

                Recursive_call(check_B,id,idd,check_R,mo,input_id,input,layout,lay_list,layout_recur)
        
        # BOX AND ROW INCEPTION
        else:
            Recursive_call(check_B,id,idd,check_R,mo,input_id,input,layout,lay_list,layout_recur)
                            

###################################################################################
# UI OP
###################################################################################
class BAGAPIE_OP_modifierDisplay(Operator):
    """Hide modifier in viewport"""
    bl_idname = "hide.viewport"
    bl_label = "Hide Viewport"

    index: bpy.props.IntProperty(default=0) # type: ignore

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        mo_type = val['name']
        avoid_string = "BagaPie_Texture"

        if mo_type == "scatter":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            scatter_node = scatt_nde_group.nodes[modifiers[1]]
            scatter_node_input_value = scatter_node.inputs[22].default_value

            if scatter_node_input_value:
                scatt_nde_group.nodes[modifiers[1]].inputs[22].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[22].default_value = True

        elif mo_type == "pointeffector":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_op = scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value

            if scatt_nde_visibility_op:
                scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[5].default_value = True

        elif mo_type == "camera":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_op = scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value

            if scatt_nde_visibility_op:
                scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[3].default_value = True

        elif mo_type == "boolean":
            if obj.modifiers[modifiers[0]].show_viewport:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_viewport = False
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = False
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = False

            else:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_viewport = True
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = True
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_viewport = True

        elif mo_type == "window":

            if modifiers[6] == "win":
                wall = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_viewport:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_viewport = False
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_viewport = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_viewport = True
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_viewport = True

            elif modifiers[6] == "wall":
                window = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_viewport:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_viewport = False
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_viewport = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_viewport = True
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_viewport = True

        elif mo_type == "wallbrick":
            if obj.type=='MESH':
                mo = modifiers[0]
                if obj.modifiers[modifiers[0]].show_viewport:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True
            else:
                mo = modifiers[1]
                if obj.modifiers[modifiers[1]].show_viewport:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True

        elif mo_type == "ivy":
            if obj.modifiers[modifiers[0]].show_viewport:
                mo = modifiers[0]
                obj.modifiers[mo].show_viewport = False
            else:
                mo = modifiers[0]
                obj.modifiers[mo].show_viewport = True

        else:
            if obj.modifiers[modifiers[0]].show_viewport:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = False
            else:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_viewport = True

        return {'FINISHED'}


class BAGAPIE_OP_modifierDisplayRender(Operator):
    """Hide modifier in render"""
    bl_idname = "hide.render"
    bl_label = "Hide Render"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        mo_type = val['name']
        avoid_string = "BagaPie_Texture"

        if mo_type == "scatter":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            scatter_node = scatt_nde_group.nodes[modifiers[1]]
            scatter_node_input_value = scatter_node.inputs[23].default_value

            if scatter_node_input_value:
                scatt_nde_group.nodes[modifiers[1]].inputs[23].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[23].default_value = True

        elif mo_type == "pointeffector":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_bool = scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value

            if scatt_nde_visibility_bool:
                scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[6].default_value = True

        elif mo_type == "camera":
            scatter_modifier = obj.modifiers.get("BagaPie_Scatter")
            scatt_nde_group = scatter_modifier.node_group
            
            scatt_nde_visibility_bool = scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value

            if scatt_nde_visibility_bool:
                scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value = False
            else:
                scatt_nde_group.nodes[modifiers[1]].inputs[4].default_value = True

        elif mo_type == "boolean":
            if obj.modifiers[modifiers[0]].show_render:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_render = False
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = False
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = False

            else:
                for mo in modifiers:
                    if mo.startswith(("BagaBool","BagaBevel")) and not mo.startswith("BagaBevelObj"):
                        obj.modifiers[mo].show_render = True
                    else:
                        bool_obj = bpy.data.objects[modifiers[5]]
                        if mo != modifiers[5]:
                            if bool_obj.modifiers[mo].show_in_editmode and mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = True
                            elif not mo.startswith("BagaSolidify"):
                                bool_obj.modifiers[mo].show_render = True

        elif mo_type == "window":

            if modifiers[6] == "win":
                wall = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_render:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_render = False
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_render = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[4] and mo != modifiers[5]:
                            obj.modifiers[mo].show_render = True
                        elif mo == modifiers[5]:
                            wall.modifiers[mo].show_render = True

            elif modifiers[6] == "wall":
                window = bpy.data.objects[modifiers[7]]
                if obj.modifiers[modifiers[0]].show_render:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_render = False
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_render = False
                else:
                    for mo in modifiers:
                        if mo.startswith("Baga") and mo != modifiers[0] and mo != modifiers[5] and mo != modifiers[7]:
                            window.modifiers[mo].show_render = True
                        elif mo == modifiers[0] and mo != modifiers[7]:
                            obj.modifiers[mo].show_render = True

        elif mo_type == "wallbrick":
            if obj.type=='MESH':
                mo = modifiers[0]
                if obj.modifiers[modifiers[0]].show_render:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True
            else:
                mo = modifiers[1]
                if obj.modifiers[modifiers[1]].show_render:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
                else:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True

        else:
            if obj.modifiers[modifiers[0]].show_render:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = False
            else:
                for mo in modifiers:
                    if mo.startswith("Baga") and not mo.startswith(avoid_string):
                        obj.modifiers[mo].show_render = True

        return {'FINISHED'}


class BAGAPIE_OP_modifierApply(Operator):
    """Apply all related modifier"""
    bl_idname = "apply.modifier"
    bl_label = "apply.modifier"

    index: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        return (bpy.context.mode == 'OBJECT')
    
    def execute(self, context):
        obj = context.object
        obj.select_set(True)
        val = json.loads(obj.bagapieList[self.index]['val'])
        modifiers = val['modifiers']
        avoid_string = "BagaPie_Texture"
        mo_type = val['name']

        if mo_type == "window":
            obj.data = obj.data.copy()
        
        for mo in modifiers:
            if mo.startswith("Baga") and not mo.startswith(avoid_string):

                if mo_type == 'wallbrick':
                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'array':
                    mo_name = obj.modifiers[mo].node_group.name

                    if "Line" in mo_name:
                        obj.modifiers[mo]["Input_10"] = gn_bool_version(1)
                    elif "Grid" in mo_name:
                        obj.modifiers[mo]["Input_14"] = gn_bool_version(1)
                    elif "Circle" in mo_name:
                        obj.modifiers[mo]["Input_21"] = gn_bool_version(1)
                    elif "Curve" in mo_name:
                        obj.modifiers[mo]["Input_13"] = gn_bool_version(1)

                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'pipes':
                    mo_name = obj.modifiers[mo].node_group.name
                
                    obj.modifiers[mo]["Input_27"] = gn_bool_version(1)

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]
                    coll = modifier["Input_13"]

                    bpy.ops.object.convert(target='MESH')
                    RemoveOBJandDeleteColl(self,context, coll)

                elif mo_type == 'cable':
                    mo_name = obj.modifiers[mo].node_group.name

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]
                    coll = modifier["Input_28"]

                    bpy.ops.object.convert(target='MESH')
                    RemoveOBJandDeleteColl(self,context, coll)

                elif mo_type == 'fence':
                    mo_name = obj.modifiers[mo].node_group.name

                    obj = context.object
                    val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
                    modifiers = val['modifiers']
                    modifier = obj.modifiers[modifiers[0]]

                    bpy.ops.object.convert(target='MESH')

                elif mo_type == 'handrail':
                    
                    bpy.ops.object.convert(target='MESH')
                    
                elif mo_type == 'beamwire':
                    mo_name = obj.modifiers[mo].node_group.name
                
                    obj.modifiers[mo]["Input_12"] = gn_bool_version(1)
                    obj.modifiers[mo].show_viewport = False # Just a way to update model
                    obj.modifiers[mo].show_viewport = True

                    bpy.ops.object.modifier_apply(modifier=mo)

                elif mo_type == 'scatter':
                    
                    bpy.ops.use.applyscatter('INVOKE_DEFAULT')

                    return {'FINISHED'}
                    
                elif mo_type == 'ivy':
                    
                    bpy.ops.use.applyivy('INVOKE_DEFAULT')

                    return {'FINISHED'}
                
                elif mo_type == "window":
                    
                    if modifiers[6] == "win":
                        if mo =="BagaWindow_Displace":
                            if obj.modifiers[mo].strength == 0.0:
                                obj.modifiers[mo].strength = 0.001

                    elif modifiers[6] == "wall":
                        win = bpy.data.objects[modifiers[7]]
                        if mo =="BagaWindow_Displace":
                            if win.modifiers[mo].strength == 0.0:
                                win.modifiers[mo].strength = 0.001

                elif mo_type == "boolean":
                    if mo =="BagaBevel":
                        if obj.modifiers[mo].width == 0.0:
                            bpy.ops.object.modifier_remove(modifier=mo)
                    elif mo =="BagaBool":
                        bpy.ops.object.modifier_apply(modifier=mo)
                
                else:
                    try:
                        bpy.ops.object.modifier_apply(modifier=mo)
                    except:
                        bpy.ops.object.modifier_remove(modifier=mo)

        if mo_type == "boolean":
            bool_obj = bpy.data.objects[modifiers[5]]
            bpy.data.objects.remove(bool_obj)

        elif mo_type == "window":
            for mod in modifiers:
                print(mod)

            if modifiers[6] == "win":############################################
                win_bool = bpy.data.objects[modifiers[4]]
                win = obj
                wall = bpy.data.objects[modifiers[7]]

                # applique le modifier sur le mur
                bpy.context.view_layer.objects.active = wall
                try:
                    bpy.ops.object.modifier_apply(modifier=modifiers[5])
                except:
                    bpy.ops.object.modifier_remove(modifier=modifiers[5])

                # delete boolean
                bpy.data.objects.remove(win_bool)

                # applique le modifier de la vitre
                bpy.context.view_layer.objects.active = win
                for mo in win.modifiers:
                    m = mo.name
                    if m.startswith("BagaWindow") and not m.startswith("BagaWindow_Bool"):
                        try:
                            bpy.ops.object.modifier_apply(modifier=m)
                        except:
                            bpy.ops.object.modifier_remove(modifier=m)

                # relève le modifier de la liste
                index = 0
                for i in range(len(wall.bagapieList)):
                    index = index + i
                    val = json.loads(wall.bagapieList[index]['val'])
                    modifiers = val['modifiers']
                    mo_type = val['name']
                    if mo_type == "window":
                        wall.bagapieList.remove(index)
                        index -=1
                bpy.context.view_layer.objects.active = obj




            elif modifiers[6] == "wall":############################################
                win_bool = bpy.data.objects[modifiers[5]]
                win = bpy.data.objects[modifiers[7]]
                wall = obj


                # applique le modifier sur le mur
                bpy.context.view_layer.objects.active = wall
                try:
                    bpy.ops.object.modifier_apply(modifier=modifiers[0])
                except:
                    bpy.ops.object.modifier_remove(modifier=modifiers[0])

                # delete boolean
                bpy.data.objects.remove(win_bool)

                # applique le modifier de la vitre
                bpy.context.view_layer.objects.active = win
                for mo in win.modifiers:
                    m = mo.name
                    if m.startswith("BagaWindow") and not m.startswith("BagaWindow_Bool"):
                        try:
                            bpy.ops.object.modifier_apply(modifier=m)
                        except:
                            bpy.ops.object.modifier_remove(modifier=m)

                # relève le modifier de la liste
                index = 0
                for i in range(len(win.bagapieList)):
                    index = index + i
                    val = json.loads(win.bagapieList[index]['val'])
                    modifiers = val['modifiers']
                    mo_type = val['name']
                    if mo_type == "window":
                        win.bagapieList.remove(index)
                        index -=1
                bpy.context.view_layer.objects.active = obj


        obj.bagapieList.remove(self.index)

        return {'FINISHED'}


class BAGAPIE_OP_addparttype(Operator):
    """WIP"""
    bl_idname = "switch.glass"
    bl_label = "switch.glass"

    index: IntProperty(
        name="G",
        description="Import or link",
        default = 1
        )

    part_type: StringProperty(
        name="G",
        description="Import or link",
        default = "GLASS"
        )

    current_state: BoolProperty(
        name="M",
        description="World or Cursor",
        default = False
        )  

    def execute(self, context):
        obj = context.object
        glass_statut = obj['line_bool_g']
        stat =glass_statut[self.index]

        if stat == gn_bool_version(1):
            glass_statut[self.index] = gn_bool_version(0)
        else:
            glass_statut[self.index] = gn_bool_version(1)

        return {'FINISHED'}


class BAGAPIE_OP_switchinput(Operator):
    """Switch GN input"""
    bl_idname = "switch.button"
    bl_label = "switch.button"

    index: bpy.props.StringProperty(name="None") # type: ignore

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = obj.modifiers[modifiers[0]]
        blender_version = bpy.app.version
        minimum_version = (3, 5, 0)
        if blender_version >= minimum_version:
            if modifier[self.index]:
                modifier[self.index] = False
            else:
                modifier[self.index] = True
        else:
            if modifier[self.index] == gn_bool_version(1):
                modifier[self.index] = gn_bool_version(0)
            else:
                modifier[self.index] = gn_bool_version(1)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class BAGAPIE_OP_switchboolnode(Operator):
    """Switch Node Bool input"""
    bl_idname = "switch.boolnode"
    bl_label = "switch.boolnode"

    index: bpy.props.IntProperty(name="None")

    def execute(self, context):
        obj = context.object
        val = json.loads(obj.bagapieList[obj.bagapieIndex]['val'])
        modifiers = val['modifiers']
        modifier = obj.modifiers[modifiers[0]]

        scatter_node = modifier.node_group.nodes.get(modifiers[1])
        blender_version = bpy.app.version
        minimum_version = (3, 5, 0)
        if blender_version >= minimum_version:
            if scatter_node.inputs[self.index].default_value:
                scatter_node.inputs[self.index].default_value = False
            else:
                scatter_node.inputs[self.index].default_value = True
        else:
            if scatter_node.inputs[self.index].default_value == gn_bool_version(1):
                scatter_node.inputs[self.index].default_value = gn_bool_version(0)
            else:
                scatter_node.inputs[self.index].default_value = gn_bool_version(1)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


###################################################################################
# DISPLAY TOOLTIPS
###################################################################################
class BagaPie_tooltips(Operator):
    """Display a tooltips"""
    bl_idname = "bagapie.tooltips"
    bl_label = "Tips"

    message: bpy.props.StringProperty(default="None") # type: ignore
    title: bpy.props.StringProperty(default="Tooltip") # type: ignore
    icon: bpy.props.StringProperty(default="INFO") # type: ignore

    def execute(self, context):
        Warning(self.message, self.title, self.icon) 
        return {'FINISHED'}


def RemoveOBJandDeleteColl(self, context, collection):
    for obj in collection.all_objects:
        collection.objects.unlink(obj)
    bpy.data.collections.remove(collection)


###################################################################################
# UI UTILS
###################################################################################
def Double_Row_Switch(ui_type = '', modifier = '', index = '', name_a ='', name_b=''):
    row = ui_type.row(align = True)
    id_a = row.operator('switch.boolcustom', depress = not modifier[index], text = name_a)
    id_a.index = index
    id_a.modifier = modifier.name
    id_b = row.operator('switch.boolcustom', depress = modifier[index], text = name_b)
    id_b.index = index
    id_b.modifier = modifier.name

def format_shortcut(kmi):
    keys = []
    if kmi.ctrl:
        keys.append("Ctrl")
    if kmi.alt:
        keys.append("Alt")
    if kmi.shift:
        keys.append("Shift")
    if kmi.oskey:
        keys.append("Cmd")
    keys.append(kmi.type.title())
    return " + ".join(keys)

def modifier_header_basic(layout):
    row_head = layout.row(align=True)
    row_head.label(text="Modifier Properties :")
    row_head.operator("wm.url_open", text="", icon = 'PLAY',emboss=False).url = "https://youtube.com/playlist?list=PLSVXpfzibQbh_qjzCP2buB2rK1lQtkQvu&si=Y4MRQn_aTIQUXOpw"


###################################################################################
# Change bool value depending on the blender version
###################################################################################
def gn_bool_version(value):
    if value == 1:
        if bpy.app.version < (3, 5, 0):
            value = 1
        else:
            value = True
    else:        
        if bpy.app.version < (3, 5, 0):
            value = 0
        else:
            value = False
    return value


classes = [
    BAGAPIE_MT_pie_menu,
    BAGAPIE_UL_List,
    BAGAPIE_PT_modifier_panel,
    BAGAPIE_OP_modifierDisplay,
    BAGAPIE_OP_modifierDisplayRender,
    BAGAPIE_OP_modifierApply,
    BAGAPIE_OP_addparttype,
    BAGAPIE_OP_switchinput,
    BAGAPIE_OP_switchboolnode,
    BagaPie_tooltips,
]