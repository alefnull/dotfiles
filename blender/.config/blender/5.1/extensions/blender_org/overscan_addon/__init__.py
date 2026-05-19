bl_info = {
    "name": "Overscan Addon",
    "author": "Eknath Kambagiri",
    "version": (1, 1, 1),
    "blender": (5, 0, 0),
    "location": "Output Properties → Overscan",
    "category": "Render",
    "description": "Adds overscan for renders",
}

import bpy
import os
import OpenImageIO as oiio
import gpu
import time
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy.app.handlers import persistent

draw_handler = None
msgbus_owner = object()

def register_properties():
    
    bpy.types.Scene.enable_overscan = bpy.props.BoolProperty(name="Enable Overscan", default=False, update=update_preview)
    
    bpy.types.Scene.overscan_left = bpy.props.IntProperty(name="Left", subtype='PIXEL',default=0, min=0, update=update_preview)
    bpy.types.Scene.overscan_right = bpy.props.IntProperty(name="Right", subtype='PIXEL',default=0, min=0, update=update_preview)
    bpy.types.Scene.overscan_bottom = bpy.props.IntProperty(name="Top", subtype='PIXEL',default=0, min=0, update=update_preview)
    bpy.types.Scene.overscan_top = bpy.props.IntProperty(name="Bottom", subtype='PIXEL',default=0, min=0, update=update_preview)
    
    bpy.types.Scene.overscan_left_pct = bpy.props.IntProperty(name="Left %", subtype='PERCENTAGE', min=0, soft_max=100, update=update_preview)
    bpy.types.Scene.overscan_right_pct = bpy.props.IntProperty(name="Right %", subtype='PERCENTAGE',min=0, soft_max=100, update=update_preview)
    bpy.types.Scene.overscan_bottom_pct = bpy.props.IntProperty(name="Top %", subtype='PERCENTAGE', min=0, soft_max=100, update=update_preview)
    bpy.types.Scene.overscan_top_pct = bpy.props.IntProperty(name="Bottom %", subtype='PERCENTAGE', min=0, soft_max=100, update=update_preview)
    
    bpy.types.Scene.overscan_preview = bpy.props.BoolProperty(name="Preview", default=False, description="Preview overscan in the viewport", update=update_preview)
    bpy.types.Scene.overscan_use_percentage = bpy.props.BoolProperty(name="Use Percentage", default=False, description="Use percentage instead of pixels", update=lambda self, ctx: on_overscan_mode_switch(self))
    
def unregister_properties():
    del bpy.types.Scene.enable_overscan
    del bpy.types.Scene.overscan_left
    del bpy.types.Scene.overscan_right
    del bpy.types.Scene.overscan_top
    del bpy.types.Scene.overscan_bottom
    del bpy.types.Scene.overscan_left_pct
    del bpy.types.Scene.overscan_right_pct
    del bpy.types.Scene.overscan_top_pct
    del bpy.types.Scene.overscan_bottom_pct
    del bpy.types.Scene.overscan_preview
    del bpy.types.Scene.overscan_use_percentage

class RENDER_PT_overscan(bpy.types.Panel):
    bl_label = "Overscan"
    bl_idname = "RENDER_PT_overscan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"
    bl_parent_id = "RENDER_PT_format"
    
    def draw_header(self, context):
        self.layout.prop(context.scene, "enable_overscan", text="")

    def draw(self, context):
        layout = self.layout
        s = context.scene
        
        layout.enabled = s.enable_overscan
        
        split = layout.split(factor=0.4)
        split.label(text="")
        split.prop(s, "overscan_use_percentage", text="Use Percentage")
                
        col = layout.column(align=True)
        
        def row(label, prop, show_px=False):
            r = col.row(align=True)
            split = r.split(factor=0.4)
            lc = split.column()
            lc.alignment = 'RIGHT'
            lc.label(text=label)
            split.prop(s, prop, text="")

        if s.overscan_use_percentage:
            row("Left",   "overscan_left_pct")
            row("Right",  "overscan_right_pct")
            row("Top",    "overscan_bottom_pct")
            row("Bottom", "overscan_top_pct")
        else:
            row("Left",   "overscan_left")
            row("Right",  "overscan_right")
            row("Top",    "overscan_bottom")
            row("Bottom", "overscan_top")                
        
        layout.separator()
        
        split = layout.split(factor=0.4)
        split.label(text="")
        split.prop(s, "overscan_preview", text="Overscan Preview")
                    
        
def overscan_enabled(scene):
    return bool(getattr(scene, "enable_overscan", False))

def get_overscan_pixels(scene, render):
    
    if not overscan_enabled(scene):
        return 0, 0, 0, 0
    
    L = scene.overscan_left
    R = scene.overscan_right
    T = scene.overscan_top
    B = scene.overscan_bottom

    if scene.overscan_use_percentage:        
        
        base_x = scene.get("_orig_res_x") or render.resolution_x
        base_y = scene.get("_orig_res_y") or render.resolution_y

        L = int(base_x * scene.overscan_left_pct /100)
        R = int(base_x * scene.overscan_right_pct /100)
        T = int(base_y * scene.overscan_top_pct /100)
        B = int(base_y * scene.overscan_bottom_pct /100)
    else:
        L = scene.overscan_left
        R = scene.overscan_right
        T = scene.overscan_top
        B = scene.overscan_bottom

    return L, R, T, B

def draw_overscan_overlay():
    scene = bpy.context.scene
    if not getattr(scene, "overscan_preview", False):
        return
    cam = scene.camera
    if cam is None: return

    area = bpy.context.area
    region = bpy.context.region
    region_data = bpy.context.region_data
    if not (area and region and region_data): return
    if region_data.view_perspective != 'CAMERA': return

    orig_x = scene.get("_orig_res_x") or scene.render.resolution_x
    orig_y = scene.get("_orig_res_y") or scene.render.resolution_y

    L, R, T, B = get_overscan_pixels(scene, scene.render)

    final_x = orig_x + L + R
    final_y = orig_y + T + B

    frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=scene)]

    frame_2d = [location_3d_to_region_2d(region, region_data, p) for p in frame]

    if None in frame_2d: return

    frame_sorted = sorted(frame_2d, key=lambda v: (v.y, v.x))
    bl, br = sorted(frame_sorted[0:2], key=lambda v: v.x)
    tl, tr = sorted(frame_sorted[2:4], key=lambda v: v.x)

    fx1 = L / final_x
    fx2 = (L + orig_x) / final_x
    fy1 = T / final_y
    fy2 = (T + orig_y) / final_y

    def lerp(a, b, t):
        return a + (b - a) * t

    inner = [
        Vector((lerp(bl.x, br.x, fx1), lerp(bl.y, tl.y, fy1))),  
        Vector((lerp(bl.x, br.x, fx2), lerp(br.y, tr.y, fy1))),  
        Vector((lerp(tl.x, tr.x, fx2), lerp(br.y, tr.y, fy2))),  
        Vector((lerp(tl.x, tr.x, fx1), lerp(bl.y, tl.y, fy2)))   
    ]

    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    gpu.state.blend_set('ALPHA')
    fill = (1.0, 0.45, 0.05, 0.1)

    outer = [bl, br, tr, tl]

    quads = [
        [outer[0], outer[1], inner[1], inner[0]],   
        [inner[3], inner[2], outer[2], outer[3]],   
        [outer[0], inner[0], inner[3], outer[3]],   
        [inner[1], outer[1], outer[2], inner[2]],   
    ]

    for q in quads:
        batch = batch_for_shader(shader, 'TRI_FAN', {"pos": [(v.x, v.y) for v in q]})
        shader.bind()
        shader.uniform_float("color", fill)
        batch.draw(shader)

    gpu.state.blend_set('NONE')
    
    dot_col = (0.0, 0.0, 0.0, 0.0)
    dash = 3; gap = 3

    def dashed(a, b):
        dist = (b - a).length
        dir = (b - a).normalized()
        pts = []
        t = 0
        while t < dist:
            s = a + dir * t
            e = a + dir * min(t + dash, dist)
            pts += [(s.x, s.y), (e.x, e.y)]
            t += dash + gap
        return pts

    pts = []
    for i in range(4):
        pts += dashed(inner[i], inner[(i + 1) % 4])

    batch = batch_for_shader(shader, 'LINES', {"pos": pts})
    shader.bind()
    shader.uniform_float("color", dot_col)
    gpu.state.line_width_set(1.0)
    batch.draw(shader)
    
def enable_overlay():
    global draw_handler
    if draw_handler is None:
        draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_overscan_overlay, (), 'WINDOW', 'POST_PIXEL'
        )
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def disable_overlay():
    global draw_handler
    if draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler, 'WINDOW')
        draw_handler = None
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

def render_start_handler(scene):
    
    if not overscan_enabled(scene):
        return
    
    scene.overscan_preview = False
    
    render = scene.render
    cam = scene.camera.data if scene.camera else None
    
    L, R, T, B = get_overscan_pixels(scene, render)

    if "_orig_res_x" in scene:
        return

    scene["_orig_res_x"] = render.resolution_x
    scene["_orig_res_y"] = render.resolution_y

    new_res_x = render.resolution_x + L + R
    new_res_y = render.resolution_y + T + B

    render.resolution_x = new_res_x
    render.resolution_y = new_res_y

    if hasattr(render, "update_render_engine"):
        render.update_render_engine()
    elif hasattr(render, "update_render_resolution"):
        render.update_render_resolution()

    #print(f"[Overscan] Resolution → {new_res_x} × {new_res_y}")

    if cam:
        if "_orig_sensor_width" not in cam:
            cam["_orig_sensor_width"] = cam.sensor_width
            
        res_max = max(scene["_orig_res_x"], scene["_orig_res_y"])
        new_res_max = max(new_res_x, new_res_y)
        
        scale = new_res_max / res_max
        cam.sensor_width = cam["_orig_sensor_width"] * scale
        #print(f"[Overscan] Sensor scaled ×{scale:.4f}")
        
    if cam:

        L, R, T, B = get_overscan_pixels(scene, render)

        orig_x = scene["_orig_res_x"]
        orig_y = scene["_orig_res_y"]

        final_x = orig_x + L + R
        final_y = orig_y + T + B

        norm = max(final_x, final_y)

        vertical_shift = (B - T) / 2
        horizontal_shift = (R - L) / 2

        shift_y = vertical_shift / norm
        shift_x = horizontal_shift / norm

        if "_orig_shift_x" not in cam:
            cam["_orig_shift_x"] = cam.shift_x
        if "_orig_shift_y" not in cam:
            cam["_orig_shift_y"] = cam.shift_y

        cam.shift_x = cam["_orig_shift_x"] + shift_x
        cam.shift_y = cam["_orig_shift_y"] + shift_y

        #print(
        #f"[Overscan] Camera shift → "
        #f"X: {shift_x:.6f}, Y: {shift_y:.6f} (norm={norm})"
    #)

def restore_resolution(scene):
    render = scene.render
    cam = scene.camera.data if scene.camera else None

    orig_x = scene.pop("_orig_res_x", None)
    orig_y = scene.pop("_orig_res_y", None)

    if orig_x and orig_y:
        render.resolution_x = orig_x
        render.resolution_y = orig_y

        if hasattr(render, "update_render_engine"):
            render.update_render_engine()
        elif hasattr(render, "update_render_resolution"):
            render.update_render_resolution()

        #print(f"[Overscan] Resolution restored → {orig_x} × {orig_y}")

    if cam and "_orig_sensor_width" in cam:
        cam.sensor_width = cam["_orig_sensor_width"]
        cam.pop("_orig_sensor_width", None)
        #print(f"[Overscan] Sensor restored")
        
    if cam and "_orig_shift_x" in cam and "_orig_shift_y" in cam:
        cam.shift_x = cam["_orig_shift_x"]
        cam.shift_y = cam["_orig_shift_y"]
        cam.pop("_orig_shift_x", None)
        cam.pop("_orig_shift_y", None)
        #print("[Overscan] Camera shift restored")

def update_exr_windows_oiio(file_path, new_dw_coords, new_dispw_coords):
    if not os.path.exists(file_path):
        print(f"[OIIO] FILE NOT FOUND: {file_path}")
        return

    input_file = output_file = None

    try:
        input_file = oiio.ImageInput.open(file_path)
        if not input_file:
            print("[OIIO] ERROR OPENING INPUT")
            return

        input_spec = input_file.spec()
        output_spec = input_spec

        dw_roi = oiio.ROI(new_dw_coords[0], new_dw_coords[2], new_dw_coords[1], new_dw_coords[3])
        disp_roi = oiio.ROI(new_dispw_coords[0], new_dispw_coords[2], new_dispw_coords[1], new_dispw_coords[3])

        oiio.set_roi(output_spec, dw_roi)
        oiio.set_roi_full(output_spec, disp_roi)

        data = input_file.read_image()
        input_file.close()

        if data is None:
            print("[OIIO] ERROR READING PIXELS")
            return

        output_file = oiio.ImageOutput.create(file_path)
        if not output_file:
            print("[OIIO] ERROR CREATING OUTPUT")
            return

        if output_file.open(file_path, output_spec):
            output_file.write_image(data)
            output_file.close()
            print(f"[OIIO] UPDATED DATA/DISPLAY WINDOW → {file_path}")
        else:
            print("[OIIO] ERROR OPENING FOR WRITE")

    except Exception as e:
        print(f"[OIIO] EXCEPTION: {e}")
    finally:
        if input_file: input_file.close()

def per_frame_metadata_handler(scene, render_data):
    
    if not overscan_enabled(scene):
        return
    
    render = scene.render
    frame = scene.frame_current

    if not render.filepath:
        return

    try:
        final_rel = render.frame_path(frame=frame)
        final_path = bpy.path.abspath(final_rel)
    except Exception:
        return

    if not final_path.lower().endswith(".exr"):
        return

    orig_x = scene.get("_orig_res_x")
    orig_y = scene.get("_orig_res_y")
    if orig_x is None or orig_y is None:
        return

    L, R, T, B = get_overscan_pixels(scene, render)

    left_x = -L
    bottom_y = -B
    right_x = orig_x + R
    top_y = orig_y + T

    NEW_DATA_WINDOW = (left_x, bottom_y, right_x, top_y)
    NEW_DISPLAY_WINDOW = (0, 0, orig_x, orig_y)

    #print(f"[OIIO] DataWindow: {NEW_DATA_WINDOW}   DisplayWindow: {NEW_DISPLAY_WINDOW}")
    update_exr_windows_oiio(final_path, NEW_DATA_WINDOW, NEW_DISPLAY_WINDOW)


def apply_preview(scene):
    
    render = scene.render
    cam = scene.camera.data if scene.camera else None

    L, R, T, B = get_overscan_pixels(scene, render)

    if not scene.overscan_preview & scene.enable_overscan:
        if "_orig_res_x" in scene:
            render.resolution_x = scene.pop("_orig_res_x")
            render.resolution_y = scene.pop("_orig_res_y")

        if cam:
            if "_orig_sensor_width" in cam:
                cam.sensor_width = cam.pop("_orig_sensor_width")
            if "_orig_shift_x" in cam:
                cam.shift_x = cam.pop("_orig_shift_x")
                cam.shift_y = cam.pop("_orig_shift_y")
        return

    if "_orig_res_x" not in scene:
        scene["_orig_res_x"] = render.resolution_x
        scene["_orig_res_y"] = render.resolution_y

    new_res_x = scene["_orig_res_x"] + L + R
    new_res_y = scene["_orig_res_y"] + T + B

    render.resolution_x = new_res_x
    render.resolution_y = new_res_y

    if cam:
        if "_orig_sensor_width" not in cam:
            cam["_orig_sensor_width"] = cam.sensor_width

        base_max = max(scene["_orig_res_x"], scene["_orig_res_y"])
        new_max  = max(new_res_x, new_res_y)
        cam.sensor_width = cam["_orig_sensor_width"] * (new_max / base_max)

        if "_orig_shift_x" not in cam:
            cam["_orig_shift_x"] = cam.shift_x
            cam["_orig_shift_y"] = cam.shift_y

        vertical_net = (B - T) / 2
        horizontal_net = (R - L) / 2
        norm = max(new_res_x, new_res_y)

        cam.shift_x = cam["_orig_shift_x"] + horizontal_net / norm
        cam.shift_y = cam["_orig_shift_y"] + vertical_net   / norm


def update_preview(self, context):
    apply_preview(context.scene)
    
    if context.scene.enable_overscan & context.scene.overscan_preview:
        enable_overlay()
    else:
        disable_overlay()    
        
    subscribe_lock_properties(context.scene)
    
def on_overscan_mode_switch(scene):
    render = scene.render

    base_x = scene.get("_orig_res_x") or render.resolution_x
    base_y = scene.get("_orig_res_y") or render.resolution_y

    if scene.overscan_use_percentage:
        # Pixels → Percentage
        scene.overscan_left_pct   = int(scene.overscan_left   / base_x *100)
        scene.overscan_right_pct  = int(scene.overscan_right  / base_x *100)
        scene.overscan_top_pct    = int(scene.overscan_top    / base_y *100)
        scene.overscan_bottom_pct = int(scene.overscan_bottom / base_y *100)
    else:
        # Percentage → Pixels
        scene.overscan_left   = int(base_x * scene.overscan_left_pct /100)
        scene.overscan_right  = int(base_x * scene.overscan_right_pct /100)
        scene.overscan_top    = int(base_y * scene.overscan_top_pct /100)
        scene.overscan_bottom = int(base_y * scene.overscan_bottom_pct /100)

    # Force preview + overlay refresh
    apply_preview(scene)

    
        
def lock_overscan_values(scene):
    if not scene.overscan_preview:
        return

    render = scene.render
    cam = scene.camera.data if scene.camera else None

    L, R, T, B = get_overscan_pixels(scene, render)

    orig_x = scene.get("_orig_res_x")
    orig_y = scene.get("_orig_res_y")

    if orig_x is not None and orig_y is not None:
        expected_x = orig_x + L + R
        expected_y = orig_y + T + B

        if render.resolution_x != expected_x:  
            render.resolution_x = expected_x

        if render.resolution_y != expected_y:
            render.resolution_y = expected_y

    if cam:
        if "_orig_sensor_width" in cam:
            expected_sensor = cam["_orig_sensor_width"] * (
                max(expected_x, expected_y) / max(orig_x, orig_y)
            )
            if cam.sensor_width != expected_sensor:
                cam.sensor_width = expected_sensor

        if "_orig_shift_x" in cam and "_orig_shift_y" in cam:
            
            L, R, T, B = get_overscan_pixels(scene, render)

            norm = max(expected_x, expected_y)

            shift_x = cam["_orig_shift_x"] + (R - L) / (2 * norm)
            shift_y = cam["_orig_shift_y"] + (B - T) / (2 * norm)

            if cam.shift_x != shift_x:
                cam.shift_x = shift_x

            if cam.shift_y != shift_y:
                cam.shift_y = shift_y


def lock_with_reset(scene):
    global lock_printed
    lock_printed = False
    lock_overscan_values(scene)


def subscribe_lock_properties(scene):
    render = scene.render
    cam = scene.camera.data if scene.camera else None

    bpy.msgbus.clear_by_owner(msgbus_owner)
    
    if not overscan_enabled(scene):
        return

    if not scene.overscan_preview:
        return

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.RenderSettings, "resolution_x"),
        owner=msgbus_owner,
        args=(),
        notify=lambda: lock_with_reset(scene)
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.RenderSettings, "resolution_y"),
        owner=msgbus_owner,
        args=(),
        notify=lambda: lock_with_reset(scene)
    )

    if cam:
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Camera, "sensor_width"),
            owner=msgbus_owner,
            args=(),
            notify=lambda: lock_with_reset(scene)
        )

        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Camera, "shift_x"),
            owner=msgbus_owner,
            args=(),
            notify=lambda: lock_with_reset(scene)
        )
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Camera, "shift_y"),
            owner=msgbus_owner,
            args=(),
            notify=lambda: lock_with_reset(scene)
        )

@persistent
def load_post_handler(dummy):
    """Re-enable overlay and msgbus locks when a .blend file is loaded."""
    scene = bpy.context.scene
    if getattr(scene, "enable_overscan", False) and getattr(scene, "overscan_preview", False):
        enable_overlay()
        subscribe_lock_properties(scene)

classes = (RENDER_PT_overscan,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_properties()

    if render_start_handler not in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.append(render_start_handler)

    if restore_resolution not in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.append(restore_resolution)

    if restore_resolution not in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.append(restore_resolution)

    if per_frame_metadata_handler not in bpy.app.handlers.render_post:
        bpy.app.handlers.render_post.append(per_frame_metadata_handler)

    if load_post_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post_handler)


def unregister():
    for handler_list in (
        bpy.app.handlers.render_init,
        bpy.app.handlers.render_post,
        bpy.app.handlers.render_complete,
        bpy.app.handlers.render_cancel,
        bpy.app.handlers.load_post,
    ):
        for handler in (render_start_handler, restore_resolution, per_frame_metadata_handler, lock_overscan_values, load_post_handler):
            if handler in handler_list:
                handler_list.remove(handler)
                
    bpy.msgbus.clear_by_owner(msgbus_owner)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    
    unregister_properties()


if __name__ == "__main__":
    register()
 