import bpy
import rna_keymap_ui
from . import __package__ as base_package

def get_addon_path(addon_name):
    for addon in bpy.context.preferences.addons:
        if str(addon_name) in addon.module:
            return addon.module
        
def get_addon_prefs():
    addon_prefs = bpy.context.preferences.addons[base_package]
    return addon_prefs.preferences

keymap_items = [
    ['Object Mode', 'EMPTY', 'wm.call_menu_pie', 'A', 'PRESS', True, False, False, 'ND_PRIMITIVES_MT_add_objects_pie_menu'],
]
def draw_keymap(self, context, layout):
    def get_pie_menu_hotkey(km, kmi_name, kmi_value):
        for i, km_item in enumerate(km.keymap_items):
            if km.keymap_items.keys()[i] == kmi_name:
                if km.keymap_items[i].properties.name == kmi_value:
                    return km_item

    def get_operator_hotkey(km, kmi_name):
        for i, km_item in enumerate(km.keymap_items):
            if km.keymap_items.keys()[i] == kmi_name:
                return km_item

    wm = context.window_manager
    kc = wm.keyconfigs.user

    for km_item in keymap_items:
        km = kc.keymaps[km_item[0]]
        operator = km_item[2]
        if operator == 'wm.call_menu_pie':
            value = km_item[-1]
            kmi = get_pie_menu_hotkey(km, 'wm.call_menu_pie', value)
        else:
            kmi = get_operator_hotkey(km, operator)
        if kmi:
            layout.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, layout, 0)

def keymap_register(wm):
    keymaps = []
    for items in keymap_items:
        (area_name, space,
            item_id, button, value,
            shift_state, ctrl_state, alt_state,
            pie_name) = items
        km = wm.keyconfigs.addon.keymaps.new(name=area_name, space_type=space)
        kmi = km.keymap_items.new(
            item_id, button, value,
            shift=shift_state, ctrl=ctrl_state, alt=alt_state
        )
        if pie_name:
            kmi.properties.name = pie_name
        keymaps.append((km, kmi))
    return keymaps


def show_hide_gizmos_update_all(self, context):
    node_group_names = []
    for obj in bpy.context.scene.objects:
        if 'non_destructive_primitive' in obj:
            value = obj['non_destructive_primitive']
            if value:
                if value not in node_group_names:
                    node_group_names.append(value)

    for node_group in bpy.data.node_groups:
        if node_group.name in node_group_names:
            show_hide_gizmos_in_node_group(node_group, self.show_gizmo)

def show_hide_gizmos_in_node_group(node_group, show_gizmo):
    for node in node_group.nodes:
        if node.type in {'GIZMO_DIAL', 'GIZMO_LINEAR'}:
            if node.mute == show_gizmo:
                node.mute = not show_gizmo        

def invert_rotation_gizmo_direction_update_all(self, context):
    node_group_names = []
    for obj in bpy.context.scene.objects:
        if 'non_destructive_primitive' in obj:
            value = obj['non_destructive_primitive']
            if value:
                if value not in node_group_names:
                    node_group_names.append(value)

    for node_group in bpy.data.node_groups: # should be made a function
        if node_group.name in node_group_names:
            invert_rotation_in_node_groupe(node_group, self.invert_rotation_gizmo_direction)

def invert_rotation_in_node_groupe(node_group, invert_rotation_gizmo_direction):
    for node in node_group.nodes:
        if node.type == 'GIZMO_DIAL': # invert rotation gizmo direction if needed
            values = list(node.inputs[2].default_value)
            if 1.0 in values and invert_rotation_gizmo_direction:
                index = values.index(1.0)
                values = [-1.0 if i == index else 0.0 for i in range(3)]
                node.inputs[2].default_value = tuple(values)
            elif -1.0 in values and not invert_rotation_gizmo_direction:
                index = values.index(-1.0)
                values = [1.0 if i == index else 0.0 for i in range(3)]
                node.inputs[2].default_value = tuple(values)