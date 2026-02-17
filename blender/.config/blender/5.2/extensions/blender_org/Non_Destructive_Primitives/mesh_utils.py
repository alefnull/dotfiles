import bpy
from .utils import get_addon_prefs
import bmesh

def calculate_scale(context, scale_property, auto_scale, scale_relative_float, custom_scale_factor=1.0):
    prefs = get_addon_prefs()
    if auto_scale:
        cursor_location = bpy.context.scene.cursor.location
        camera_pivot_center = context.region_data.view_location
        camera_view_distance = context.area.spaces.active.region_3d.view_distance

        #Need to calculate the distance from the camera pivot center to the cursor in order to compensate for the camera pivot offset from the cursor, otherwise the scale will be off
        distance_to_cursor = (cursor_location - camera_pivot_center).length
        camera_view_distance = (camera_view_distance - distance_to_cursor)

        scale = camera_view_distance / scale_relative_float * custom_scale_factor
        if scale >= 10.0:
            scale = round(scale / 5) * 5  #Round to nearest multiple of 5
        elif scale >= 1.0:
            scale = round(scale * 2) / 2  #Round to nearest 0.5
        else:                                                   
            scale = scale * 1.75  #Add an 75% extra scale to make it easier to see
            scale_levels = [1.0, 0.75, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.0025, 0.001]
            for level in scale_levels:
                if scale >= level:
                    scale = level
                    break
            #Make sure the scale is never 0
            min_scale = prefs.min_scale
            if scale < min_scale:
                scale = min_scale
    else:
        scale = scale_property
    return scale

def obj_to_mesh_in_edit_mode(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = obj.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, depsgraph=depsgraph)

    bm = bmesh.from_edit_mesh(obj.data)
    bm.clear()
    bm.from_mesh(mesh_from_eval)
    bmesh.update_edit_mesh(obj.data)

def on_edit_mode_apply_nd_primitive():
    # import time
    # exec_time = time.time() 
    prefs = get_addon_prefs()
    modifier_exists = False

    if bpy.context.object.mode == "EDIT":
        for obj in bpy.context.selected_objects:
            if 'non_destructive_primitive' in obj:
                if obj and obj.type == 'MESH' and obj.modifiers:
                    mod_name = obj['non_destructive_primitive']
                    if mod_name:
                        for mod in obj.modifiers:
                            if mod.name == mod_name:
                                modifier_exists = True
                                if mod.show_viewport:
                                    primitive_modifier = mod
                                    modifiers_that_is_show_in_edit_mode = []
                                    
                                    for mod in obj.modifiers:
                                        if mod.show_in_editmode:
                                            if not mod.name == mod_name: 
                                                modifiers_that_is_show_in_edit_mode.append(mod)
                                                mod.show_in_editmode = False
                    
                                    primitive_modifier.show_in_editmode = True

                                    if prefs.apply_modifier_on_enter_edit_mode:
                                        obj_to_mesh_in_edit_mode(obj)

                                        if prefs.delete_modifier:
                                            obj.modifiers.remove(primitive_modifier)
                                        else:
                                            primitive_modifier.show_viewport = False

                                    #reset show in edit mode
                                    for mod in modifiers_that_is_show_in_edit_mode:
                                        mod.show_in_editmode = True
                if not modifier_exists:
                    del obj['non_destructive_primitive']

    # print(f"Total Time: {time.time() - exec_time:.4f} seconds")

def AddModCylinder(context, segment_amount, use_relative_scale, scale_relative_float, scale_property):
    if bpy.context.mode == 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD',  scale=(1, 1, 1))    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.edge_collapse()
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(1, 0, 0),  "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'VERTEX'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0),})
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 2),  "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'VERTEX'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0),})
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-1, -0, -0),  "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'VERTEX'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0),})
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(-0, -0, -1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'VERTEX'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.modifier_add(type='SCREW')
    bpy.context.object.modifiers["Screw"].name = "Mod Cylinder"
    bpy.context.object.modifiers["Mod Cylinder"].use_smooth_shade = True
    bpy.context.object.modifiers["Mod Cylinder"].steps = segment_amount
    bpy.context.object.modifiers["Mod Cylinder"].use_normal_calculate = True
    bpy.context.object.modifiers["Mod Cylinder"].use_normal_flip = True

    scale = calculate_scale(context, scale_property, use_relative_scale, scale_relative_float, custom_scale_factor=0.5)
    if use_relative_scale==False:
            scale = scale*0.5
    obj = bpy.context.active_object
    obj.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.object.modifiers["Mod Cylinder"].use_merge_vertices = True
    bpy.context.object.modifiers["Mod Cylinder"].merge_threshold = scale * 0.1
    return obj

   
