import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, FloatVectorProperty, StringProperty, EnumProperty
from .import __package__ as base_package
from .utils import draw_keymap, show_hide_gizmos_update_all, invert_rotation_gizmo_direction_update_all
from .add_menu import update_add_menu

BLENDER_VERSION = bpy.app.version
CONST_ITEMS = [("Grid", "MESH_PLANE"),
                ("Cube", "MESH_CUBE"),
                ("Circle", "MESH_CIRCLE"),
                ("UV Sphere", "MESH_UVSPHERE"),
                ("Ico Sphere", "MESH_ICOSPHERE"),
                ("Cylinder", "MESH_CYLINDER"),
                ("Cone", "MESH_CONE"),
                ("Torus", "MESH_TORUS"),
                ("Quad Sphere", "SPHERE"),
                ("Capsule", "MESH_CAPSULE"),
                ("Quad Capsule", "META_CAPSULE"),
                ("Mod Cylinder", "MOD_SCREW"),
                ("Spiral", "MOD_SCREW"),
                ("Tube", "SURFACE_NCYLINDER"),
                ("Other", "ADD"),
                # (".blend", "BLENDER"),
                ("CUSTOM_OP", "FILE_SCRIPT")]

add_pie_menu_items = [
    (f"{item[0]}", item[0], "", item[1], index)
    for index, item in enumerate(CONST_ITEMS)]

class ND_Primitives_Preferences(bpy.types.AddonPreferences):
    bl_idname = base_package 

    show_in_menu: EnumProperty(name="ND Primitives in", items=[("ADD_MESH", "Mesh Menu", "", "OUTLINER_OB_MESH", 1),
                                                           ("OWN_CATEGORY_IN_ADD_MENU", "Menu in Mesh", "", "FILE_3D", 0),
                                                           ("OWN_MENU_CATEGORY", "Add Menu", "", "OBJECT_DATA", 2),
                                                           ("NONE", "None", "")], default="ADD_MESH", update=update_add_menu)# type: ignore
    # use_relative_scale: BoolProperty(name="Auto Scale", default=True, description="Default to Relative Scale Value") # type: ignore
    # default_scale: FloatProperty(name="Default Size", default=1.0, min=0.1, max=10.0, unit='LENGTH', description="Default Regular Scale Size Value") # type: ignore
    min_scale: FloatProperty(name="Min Size", default=0.01, min=0.0001, max=10.0, unit='LENGTH', description="Auto Scale Min Size Value") # type: ignore
    apply_modifier_on_enter_edit_mode: BoolProperty(name="Auto Apply Modifier in Edit Mode", default=True, description="Begin editing the mesh, without needing to apply the modifier once entering edit mode") # type: ignore
    delete_modifier: BoolProperty(name="Delete Modifier", default=False, description="Delete the modifier when entering edit mode") # type: ignore
    show_gizmo: BoolProperty(name="Show Gizmos", default=True, description="Show the gizmos", update=show_hide_gizmos_update_all) # type: ignore
    auto_swith_to_modifier_tab: BoolProperty(name="Auto Switch to Modifier Tab", default=True, description="Switch to the modifier tab when adding a primitive") # type: ignore
    invert_rotation_gizmo_direction: BoolProperty(name="Invert Rotation Gizmo Direction", default=False, description="Invert the rotation gizmo direction" ,update=invert_rotation_gizmo_direction_update_all) # type: ignore
    origin_at_bottom: BoolProperty(name="Origin at Bottom", default=False, description="Set the origin at the bottom of the primitve by default, restart Blender to take effect") # type: ignore

    pie_add_left: EnumProperty(name="Left", items=add_pie_menu_items, default="UV Sphere") # type: ignore
    pie_add_right: EnumProperty(name="Right", items=add_pie_menu_items, default="Cube") # type: ignore
    pie_add_bottom: EnumProperty(name="Bottom", items=add_pie_menu_items, default="Cylinder") # type: ignore
    pie_add_top: EnumProperty(name="Top", items=add_pie_menu_items, default="Grid") # type: ignore
    pie_add_top_left: EnumProperty(name="Top Left", items=add_pie_menu_items, default="Mod Cylinder") # type: ignore
    pie_add_top_right: EnumProperty(name="Top Right", items=add_pie_menu_items, default="Other") # type: ignore
    pie_add_bottom_left: EnumProperty(name="Bottom Left", items=add_pie_menu_items, default="Quad Sphere") # type: ignore
    pie_add_bottom_right: EnumProperty(name="Bottom Right", items=add_pie_menu_items, default="Circle") # type: ignore
    
    pie_add_custom_op_left: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_left: StringProperty(default="") # type: ignore

    pie_add_custom_op_right: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_right: StringProperty(default="") # type: ignore

    pie_add_custom_op_top: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_top: StringProperty(default="") # type: ignore

    pie_add_custom_op_bottom: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_bottom: StringProperty(default="") # type: ignore

    pie_add_custom_op_top_left: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_top_left: StringProperty(default="") # type: ignore

    pie_add_custom_op_top_right: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_top_right: StringProperty(default="") # type: ignore

    pie_add_custom_op_bottom_left: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_bottom_left: StringProperty(default="") # type: ignore

    pie_add_custom_op_bottom_right: StringProperty(default="") # type: ignore
    pie_add_custom_op_name_bottom_right: StringProperty(default="") # type: ignore
    
    def draw(self, context):
        layout = self.layout

        # General settings
        layout.label(text="General Settings:")
        box = layout.box()
        row = box.row()
        row.prop(self, "apply_modifier_on_enter_edit_mode")
        sub_row = row.row()
        sub_row.enabled = self.apply_modifier_on_enter_edit_mode
        sub_row.prop(self, "delete_modifier")
        row = box.row()
        row.prop(self, "auto_swith_to_modifier_tab")

        if BLENDER_VERSION >= (4, 3, 0):
            row = box.row()
            row.prop(self, "show_gizmo")
            sub_row = row.row()
            sub_row.enabled = self.show_gizmo
            sub_row.prop(self, "invert_rotation_gizmo_direction")
        else:
            row = box.row()
            row.label(text="Gizmos is only available in Blender 4.3 and up", icon="ERROR")

        row = box.row()
        row.label(text="Defaults:")
        row = box.row()
        row.prop(self, "origin_at_bottom")
        row = box.row()
        row.label(text="Min Auto Scale:")
        row.scale_x = 0.55
        row.alignment = 'LEFT'
        row.prop(self, "min_scale")


        # menu
        row = layout.row()
        row.alignment = 'LEFT'
        row.scale_x = 1.25
        row.label(text="Menu Settings:")
        row.prop(self, "show_in_menu", text="Show ND Primitives in")

        box = layout.box()
        row.alignment = 'LEFT'
        row.scale_x = 1.2
        row = box.row()

        # pie menu customization
        draw_keymap(self, context, box)
        # Pie menu customization layout to resemble a pie menu structure

        spacer1_X = 0.55
        spacer2_X = 0.75
        all_X = 1.0
        all_Y = 1.2

        positions = [
            ("Top", "pie_add_top"),
            ("Top-Left", "pie_add_top_left", "pie_add_top_right"),
            ("Left", "pie_add_left", "pie_add_right"),
            ("Bottom-Left", "pie_add_bottom_left", "pie_add_bottom_right"),
            ("Bottom", "pie_add_bottom")
        ]

        def is_pie_menu_active():
            wm = bpy.context.window_manager
            keyconfig = wm.keyconfigs.user
            km = keyconfig.keymaps['Object Mode']
            kmi = km.keymap_items['wm.call_menu_pie']
            return kmi.active 

        for index, pos in enumerate(positions):
            if index != 0:
                box.separator()
            row = box.row()
            row.alignment = 'CENTER'
            row.scale_x = all_X
            row.scale_y = all_Y
            keymap_active = is_pie_menu_active()
            row.enabled = keymap_active
            if len(pos) == 2:
                row.prop(self, pos[1], text="")
            else:
                row.prop(self, pos[1], text="")
                spacer = row.row()
                spacer.scale_x = spacer1_X if "Top" in pos[0] or "Bottom" in pos[0] else spacer2_X
                spacer.label(text=" ")
                row.prop(self, pos[2], text="")


        # Custom Operators for all positions
        custom_positions = [
            ("pie_add_left", "pie_add_custom_op_left", "pie_add_custom_op_name_left"),
            ("pie_add_right", "pie_add_custom_op_right", "pie_add_custom_op_name_right"),
            ("pie_add_bottom", "pie_add_custom_op_bottom", "pie_add_custom_op_name_bottom"),
            ("pie_add_top", "pie_add_custom_op_top", "pie_add_custom_op_name_top"),
            ("pie_add_top_left", "pie_add_custom_op_top_left", "pie_add_custom_op_name_top_left"),
            ("pie_add_top_right", "pie_add_custom_op_top_right", "pie_add_custom_op_name_top_right"),
            ("pie_add_bottom_left", "pie_add_custom_op_bottom_left", "pie_add_custom_op_name_bottom_left"),
            ("pie_add_bottom_right", "pie_add_custom_op_bottom_right", "pie_add_custom_op_name_bottom_right")
        ]

        for position, custom_op, custom_op_name in custom_positions:
            if getattr(self, position) == "CUSTOM_OP":
                sub_row = box.row()
                sub_row.alignment = 'LEFT'
                sub_row.prop(self, custom_op, text="Custom Operator" + " " + position.replace("pie_add_", ""))
                sub_row.prop(self, custom_op_name, text="Name")

