bl_info = {
    "name": "Light Generator",
    "author": "The French Monkey",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "Sidebar > Light Generator",
    "description": "Generate lights with advanced distribution",
    "category": "Lighting",
    "license": "GPL-3.0-or-later",
}

import bpy
import random
import math
import os
import json
from mathutils import Vector, Euler

GENERATOR_NAME = "LightGenerator"

# ------------------------------
# Add-on Data Path / Preset File
# ------------------------------

def get_addon_data_path():
    addon_id = "light_generator"
    try:
        path = bpy.utils.extension_path_user(addon_id)
    except Exception:
        path = bpy.utils.user_resource('SCRIPTS', path="addons/light_generator", create=True)
    os.makedirs(path, exist_ok=True)
    return path

def get_preset_file():
    return os.path.join(get_addon_data_path(), "light_generator_presets.json")

# ------------------------------
# Utility Functions
# ------------------------------

def get_active_light_generator(context):
    for obj in context.selected_objects:
        if obj.name.startswith(GENERATOR_NAME) and obj.type == 'EMPTY':
            return obj
        if obj.parent and obj.parent.name.startswith(GENERATOR_NAME) and obj.parent.type == 'EMPTY':
            return obj.parent
    return None

def ensure_new_light_generator(context):
    i = 1
    while f"{GENERATOR_NAME}_{i:02d}" in bpy.data.objects:
        i += 1
    empty = bpy.data.objects.new(f"{GENERATOR_NAME}_{i:02d}", None)
    empty.empty_display_type = 'ARROWS'
    context.collection.objects.link(empty)
    for obj in list(context.selected_objects):
        obj.select_set(False)

    empty.select_set(True)
    context.view_layer.objects.active = empty
    return empty

def get_target_location(context):
    s = context.scene.light_gen_settings
    if s.UseTargetObject and s.TargetObject:
        return s.TargetObject.location.copy()
    return Vector((0, 0, 0))

def point_object_at(obj, target_location):
    direction = target_location - obj.location
    if direction.length == 0:
        return
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler('XYZ')

def point_object_down(obj):
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = (0.0, 0.0, 0.0)

# ------------------------------
# Position Generators
# ------------------------------

def compute_position(index, total, target, distance, distance_randomizer, z_offset, spacing_method, seed):
    random.seed(seed + index)
    dist = distance + random.uniform(-distance_randomizer, distance_randomizer)

    if spacing_method == 'Random':
        theta = random.uniform(0, math.pi)
        phi = random.uniform(0, 2*math.pi)
        direction = Vector((math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta))).normalized()
        pos = target + direction*dist
        pos.z += z_offset
        return pos
    elif spacing_method == 'Ring':
        angle = (2*math.pi/total)*index
        x = math.cos(angle)*dist
        y = math.sin(angle)*dist
        z = z_offset
        return target + Vector((x, y, z))
    elif spacing_method == 'Sphere Grid':
        lat_count = int(math.sqrt(total))
        lon_count = int(math.ceil(total/lat_count))
        lat = math.pi*(index//lon_count)/(lat_count-1) if lat_count>1 else 0
        lon = 2*math.pi*(index%lon_count)/lon_count
        x = dist*math.sin(lat)*math.cos(lon)
        y = dist*math.sin(lat)*math.sin(lon)
        z = dist*math.cos(lat)+z_offset
        return target + Vector((x, y, z))
    elif spacing_method == 'Spiral':
        angle = index*(2*math.pi/total)*5
        z = z_offset + (index/total)*dist
        x = math.cos(angle)*dist
        y = math.sin(angle)*dist
        return target + Vector((x, y, z))
    elif spacing_method == 'Grid':
        cols = int(math.ceil(math.sqrt(total)))
        rows = int(math.ceil(total/cols))
        row = index // cols
        col = index % cols
        spacing = dist*2
        x = (col-(cols-1)/2)*spacing
        y = (row-(rows-1)/2)*spacing
        z = z_offset
        return target + Vector((x, y, z))
    elif spacing_method == 'Line':
        spacing = dist*2
        x = index*spacing-(total-1)*spacing/2
        return target + Vector((x, 0, z_offset))
    elif spacing_method == 'Dome':
        theta = random.uniform(0, math.pi/2)
        phi = random.uniform(0, 2*math.pi)
        direction = Vector((math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta))).normalized()
        pos = target + direction*dist
        pos.z += z_offset
        return pos
    return target

# ------------------------------
# Presets Functions
# ------------------------------

def save_preset_to_file(preset_dict):
    presets = []
    preset_file = get_preset_file()
    if os.path.exists(preset_file):
        with open(preset_file, "r") as f:
            try:
                presets = json.load(f)
            except:
                presets = []

    presets = [p for p in presets if p['name'] != preset_dict['name']]
    presets.append(preset_dict)
    with open(preset_file, "w") as f:
        json.dump(presets, f, indent=4)


def get_available_presets():
    preset_file = get_preset_file()
    if not os.path.exists(preset_file):
        return []
    with open(preset_file, "r") as f:
        try:
            presets = json.load(f)
            return [p['name'] for p in presets]
        except:
            return []

# ------------------------------
# Update Lights
# ------------------------------

def update_lights(context, force_generator=None):
    s = context.scene.light_gen_settings
    generator = force_generator or get_active_light_generator(context)
    if not generator:
        return

    target = get_target_location(context)

    if s.SpacingMethod == "Preset" and s.SelectedPreset != "":
        preset_file = get_preset_file()
        if not os.path.exists(preset_file):
            return

        with open(preset_file, "r") as f:
            try:
                presets = json.load(f)
            except Exception:
                return

        preset_data = next((p for p in presets if p["name"] == s.SelectedPreset), None)
        if not preset_data:
            return

        for obj in list(generator.children):
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj, do_unlink=True)

        for ldata in preset_data["Lights"]:
            light_data = bpy.data.lights.new(name=f"LG_{ldata['type']}", type=ldata["type"])
            light_obj = bpy.data.objects.new(name=f"LG_LightObj_{ldata['type']}", object_data=light_data)
            context.collection.objects.link(light_obj)
            light_obj.parent = generator

            light_obj.location = Vector(ldata["location"])
            light_obj.rotation_mode = 'XYZ'
            light_obj.rotation_euler = Euler(ldata["rotation"])

            light = light_obj.data
            light.color = ldata["color"]
            light.energy = ldata["energy"]

            if light.type == 'AREA':
                light.shape = ldata.get("shape", "SQUARE")
                if light.shape == "RECTANGLE":
                    light.size = ldata.get("size", 10)
                    light.size_y = ldata.get("size_y", 10)
                else:
                    light.size = ldata.get("size", 10)
            elif light.type == 'POINT':
                light.shadow_soft_size = ldata.get("radius", 1)
            elif light.type == 'SPOT':
                light.spot_size = ldata.get("spot_size", 0.785)
                light.spot_blend = ldata.get("spot_blend", 0.15)
                light.shadow_soft_size = ldata.get("radius", 1)
        return

    existing_lights = [obj for obj in generator.children if obj.type == 'LIGHT']

    while len(existing_lights) < s.LightCount:
        light_data = bpy.data.lights.new(name=f"LG_Light_{len(existing_lights)}", type=s.LightType)
        light_obj = bpy.data.objects.new(name=f"LG_LightObj_{len(existing_lights)}", object_data=light_data)
        light_obj.parent = generator
        context.collection.objects.link(light_obj)
        light_obj["lg_initialized"] = False
        existing_lights.append(light_obj)

    while len(existing_lights) > s.LightCount:
        obj = existing_lights.pop()
        bpy.data.objects.remove(obj, do_unlink=True)

    for i, obj in enumerate(existing_lights):
        obj.data.type = s.LightType
        pos = compute_position(
            i, len(existing_lights), target, s.DistanceFromTarget, s.DistanceRandomizer,
            s.ZOffset, s.SpacingMethod, s.RandomSeed
        )
        obj.location = pos

        if s.SpacingMethod in {'Grid', 'Line'} and s.GridLinePointDown:
            point_object_down(obj)
        else:
            point_object_at(obj, target)

        light = obj.data

        if not obj.get("lg_initialized", False):
            light.color = (1.0, 1.0, 1.0)
            obj["lg_initialized"] = True

        light.energy = (
            random.Random(s.PowerSeed + i).uniform(s.PowerMin, s.PowerMax)
            if s.RandomizeLightPower else (s.PowerMin + s.PowerMax) / 2
        )

        if s.LightType == 'AREA':
            light.shape = s.AreaShape
            if s.AreaShape == 'RECTANGLE':
                light.size = s.AreaSizeX
                light.size_y = s.AreaSizeY
            else:
                light.size = s.LightSize
        elif s.LightType == 'POINT':
            light.shadow_soft_size = s.Radius
        elif s.LightType == 'SPOT':
            light.spot_size = math.radians(s.SpotSize)
            light.spot_blend = s.SpotBlend
            light.shadow_soft_size = s.Radius
            
def select_all_lights_in_generator(context):
    gen = get_active_light_generator(context)
    if not gen:
        return
    for obj in list(context.selected_objects):
        obj.select_set(False)
    gen.select_set(True)
    context.view_layer.objects.active = gen
    for obj in gen.children:
        if obj.type == 'LIGHT':
            obj.select_set(True)
            
# ------------------------------
# Preset Menu
# ------------------------------

class LIGHT_MT_presets_menu(bpy.types.Menu):
    bl_label="Light Presets"
    bl_idname="LIGHT_MT_presets_menu"
    def draw(self, context):
        layout = self.layout
        presets = get_available_presets()
        if not presets:
            layout.label(text="No presets saved")
        else:
            for p in presets:
                op = layout.operator("light.select_preset", text=p)
                op.preset_name = p

class LIGHT_OT_select_preset(bpy.types.Operator):
    bl_idname = "light.select_preset"
    bl_label = "Select Preset"
    preset_name: bpy.props.StringProperty()
    def execute(self, context):
        s = context.scene.light_gen_settings
        s.SelectedPreset = self.preset_name
        update_lights(context)
        return {'FINISHED'}

# ------------------------------
# Operators
# ------------------------------

class LIGHT_OT_generate_lights(bpy.types.Operator):
    bl_idname = "light.generate_lights"
    bl_label = "Generate Lights"

    def execute(self, context):
        generator = get_active_light_generator(context)
        if not generator:
            generator = ensure_new_light_generator(context)
            self.report({'INFO'}, f"Created new Light Generator: {generator.name}")

        update_lights(context, force_generator=generator)

        s = context.scene.light_gen_settings
        if s.SelectAllLights:
            select_all_lights_in_generator(context)

        return {'FINISHED'}

class LIGHT_OT_clear_lights(bpy.types.Operator):
    bl_idname = "light.clear_lights"
    bl_label = "Delete Lights"

    def execute(self, context):
        generator = get_active_light_generator(context)
        if not generator:
            self.report({'WARNING'}, "No Light Generator selected.")
            return {'CANCELLED'}

        for obj in list(generator.children):
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj, do_unlink=True)

        bpy.data.objects.remove(generator, do_unlink=True)

        self.report({'INFO'}, "Light Generator and its lights deleted.")
        return {'FINISHED'}

class LIGHT_OT_save_preset(bpy.types.Operator):
    bl_idname = "light.save_preset"
    bl_label = "Save Current Lights as Preset"
    preset_name: bpy.props.StringProperty(name="Preset Name")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        generator = get_active_light_generator(context)
        if not generator:
            self.report({'WARNING'}, "No active Light Generator selected.")
            return {'CANCELLED'}

        lights = []
        for obj in generator.children:
            if obj.type != 'LIGHT':
                continue
            light = obj.data
            lights.append({
                "type": light.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "color": list(light.color),
                "energy": light.energy,
                "shape": getattr(light, 'shape', None),
                "size": getattr(light, 'size', 0),
                "size_y": getattr(light, 'size_y', 0),
                "radius": getattr(light, 'shadow_soft_size', 0),
                "spot_size": getattr(light, 'spot_size', 0),
                "spot_blend": getattr(light, 'spot_blend', 0),
            })

        if not lights:
            self.report({'WARNING'}, "No lights found under the active Light Generator.")
            return {'CANCELLED'}

        save_preset_to_file({"name": self.preset_name, "Lights": lights})
        self.report({'INFO'}, f"Preset '{self.preset_name}' saved from {generator.name}!")
        return {'FINISHED'}

class LIGHT_OT_delete_preset(bpy.types.Operator):
    bl_idname = "light.delete_preset"
    bl_label = "Delete Selected Preset"
    bl_description = "Remove the currently selected light preset"

    def execute(self, context):
        s = context.scene.light_gen_settings
        preset_name = s.SelectedPreset

        if not preset_name:
            self.report({'WARNING'}, "No preset selected.")
            return {'CANCELLED'}

        preset_file = get_preset_file()
        if not os.path.exists(preset_file):
            self.report({'WARNING'}, "No preset file found.")
            return {'CANCELLED'}

        try:
            with open(preset_file, "r") as f:
                presets = json.load(f)
        except Exception:
            self.report({'ERROR'}, "Failed to read presets file.")
            return {'CANCELLED'}

        new_presets = [p for p in presets if p.get("name") != preset_name]

        if len(new_presets) == len(presets):
            self.report({'WARNING'}, f"No preset named '{preset_name}' found.")
            return {'CANCELLED'}

        with open(preset_file, "w") as f:
            json.dump(new_presets, f, indent=4)

        s.SelectedPreset = ""  
        self.report({'INFO'}, f"Preset '{preset_name}' deleted.")
        return {'FINISHED'}
    
# ------------------------------
# Properties
# ------------------------------

class LightGenSettings(bpy.types.PropertyGroup):
    LightCount: bpy.props.IntProperty(name="Light Count", default=1, min=1, max=200, update=lambda self,c:(update_lights(c), select_all_lights_in_generator(c) if c.scene.light_gen_settings.SelectAllLights else None), subtype='FACTOR')
    DistanceFromTarget: bpy.props.FloatProperty(name="Distance From Target", default=25, min=0, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')
    DistanceRandomizer: bpy.props.FloatProperty(name="Distance Randomizer", default=0.0, min=-100, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')
    ZOffset: bpy.props.FloatProperty(name="Z Offset", default=0.0, min=-100, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')

    LightType: bpy.props.EnumProperty(name="Light Type", items=[('POINT','Point','Point Light'),('AREA','Area','Area Light'),('SPOT','Spot','Spot Light')], default='POINT', update=lambda self,c:update_lights(c))
    AreaShape: bpy.props.EnumProperty(name="Area Shape", items=[('SQUARE','Square','Square'),('DISK','Disk','Disk'),('RECTANGLE','Rectangle','Rectangle')], default='SQUARE', update=lambda self,c:update_lights(c))
    LightSize: bpy.props.FloatProperty(name="Size", default=10, min=0.01, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')
    AreaSizeX: bpy.props.FloatProperty(name="Size X", default=10, min=0.01, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')
    AreaSizeY: bpy.props.FloatProperty(name="Size Y", default=10, min=0.01, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')
    Radius: bpy.props.FloatProperty(name="Radius", default=10, min=0.01, max=100, update=lambda self,c:update_lights(c), subtype='FACTOR')

    RandomizeLightPower: bpy.props.BoolProperty(name="Randomize Light Power", default=False, update=lambda self,c:update_lights(c))
    PowerMin: bpy.props.FloatProperty(name="Min Power", default=0.0, min=0.0, max=10000, update=lambda self,c:update_lights(c), subtype='FACTOR')
    PowerMax: bpy.props.FloatProperty(name="Max Power", default=100.0, min=0.0, max=10000, update=lambda self,c:update_lights(c), subtype='FACTOR')
    PowerSeed: bpy.props.IntProperty(name="Seed", default=0, min=0, max=1000, update=lambda self,c:update_lights(c))
    
    def update_spacing(self, context):
        if self.SpacingMethod != "Preset":
            update_lights(context)

    SpacingMethod: bpy.props.EnumProperty(name="Spacing Method", items=[
        ('Random','Random','Random placement'),
        ('Ring','Ring','Even circle'),
        ('Sphere Grid','Sphere Grid','Even sphere'),
        ('Spiral','Spiral','Spiral layout'),
        ('Grid','Grid','Square grid layout'),
        ('Line','Line','Lights in a line'),
        ('Dome','Dome','Upper hemisphere'),
        ('Preset','Preset','Use a saved preset')
    ], default='Random', update=update_spacing)

    GridLinePointDown: bpy.props.BoolProperty(name="Point Down Instead of Center", default=False, update=lambda self,c:update_lights(c))
    RandomSeed: bpy.props.IntProperty(name="Seed", default=0, min=0, max=1000, update=lambda self,c:update_lights(c), subtype='FACTOR')

    UseTargetObject: bpy.props.BoolProperty(name="Use Target Object", default=False, update=lambda self,c:update_lights(c))
    TargetObject: bpy.props.PointerProperty(name="Target Object", type=bpy.types.Object, update=lambda self,c:update_lights(c))

    SpotSize: bpy.props.FloatProperty(name="Spot Size", default=45.0, min=1.0, max=180.0, update=lambda self,c:update_lights(c), subtype='FACTOR')
    SpotBlend: bpy.props.FloatProperty(name="Spot Blend", default=0.15, min=0.0, max=1.0, update=lambda self,c:update_lights(c), subtype='FACTOR')

    SelectedPreset: bpy.props.StringProperty(name="Selected Preset", default="")
    
    def _update_select_all_lights(self, context):
        if self.SelectAllLights:
            select_all_lights_in_generator(context)
    
    SelectAllLights: bpy.props.BoolProperty(name="Select All Lights", default=False, update=_update_select_all_lights)

# ------------------------------
# Panel
# ------------------------------

class LIGHT_PT_generator_panel(bpy.types.Panel):
    bl_label = "Light Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Light Generator'

    def draw(self, context):
        layout = self.layout
        s = context.scene.light_gen_settings
        active_gen = get_active_light_generator(context)

        layout.operator("light.generate_lights", icon="LIGHT_DATA")
        layout.operator("light.save_preset", icon="FILE_TICK")

        row = layout.row(align=True)
        row.prop(s, "SelectAllLights", toggle=True)

        if s.SelectAllLights and active_gen:
            selected_lights = [o for o in context.selected_objects if o.type == 'LIGHT']
            gen_lights = [o for o in active_gen.children if o.type == 'LIGHT']

            if set(selected_lights) != set(gen_lights):
                def _delayed_select():
                    if bpy.context.scene.light_gen_settings.SelectAllLights:
                        select_all_lights_in_generator(bpy.context)
                    return None  
                bpy.app.timers.register(_delayed_select, first_interval=0.05)
                
        layout.separator()
        layout.enabled = bool(active_gen)
        layout.prop(s, "SpacingMethod")

        if s.SpacingMethod in {'Grid', 'Line'}:
            layout.prop(s, "GridLinePointDown", toggle=True)

        if s.SpacingMethod == "Preset":
            layout.menu(
                "LIGHT_MT_presets_menu",
                text=s.SelectedPreset if s.SelectedPreset else "Select Preset"
            )
            row = layout.row(align=True)
            row.operator("light.delete_preset", text="Delete Selected Preset", icon="TRASH")

        else:
            layout.prop(s, "LightCount")
            if s.SpacingMethod == "Random":
                layout.prop(s, "RandomSeed")
            layout.prop(s, "DistanceFromTarget")
            layout.prop(s, "DistanceRandomizer")
            layout.prop(s, "ZOffset")
            layout.separator()

            layout.prop(s, "LightType", expand=True)

            if s.LightType == "AREA":
                layout.prop(s, "AreaShape", expand=True)
                if s.AreaShape == "RECTANGLE":
                    layout.prop(s, "AreaSizeX")
                    layout.prop(s, "AreaSizeY")
                else:
                    layout.prop(s, "LightSize")
            elif s.LightType in {'POINT', 'SPOT'}:
                layout.prop(s, "Radius")
            if s.LightType == "SPOT":
                layout.prop(s, "SpotSize")
                layout.prop(s, "SpotBlend")
                
            layout.separator()
            layout.prop(s, "RandomizeLightPower", toggle=True)
            if s.RandomizeLightPower:
                layout.prop(s, "PowerMin")
                layout.prop(s, "PowerMax")
                layout.prop(s, "PowerSeed")

            layout.prop(s, "UseTargetObject", toggle=True)
            if s.UseTargetObject:
                layout.prop(s, "TargetObject")

        layout.separator()

        layout.enabled = True
        layout.operator("light.clear_lights", icon="TRASH")

        layout.separator(factor=0.5)

        if active_gen:
            layout.label(text=f"Editing: {active_gen.name}", icon="EMPTY_AXIS")
        else:
            layout.label(text="No Light Generator selected", icon="INFO")

# ------------------------------
# Registration
# ------------------------------

classes = (
    LightGenSettings,
    LIGHT_OT_generate_lights,
    LIGHT_OT_clear_lights,
    LIGHT_OT_save_preset,
    LIGHT_OT_delete_preset,  
    LIGHT_PT_generator_panel,
    LIGHT_MT_presets_menu,
    LIGHT_OT_select_preset
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.light_gen_settings = bpy.props.PointerProperty(type=LightGenSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "light_gen_settings"):
        del bpy.types.Scene.light_gen_settings

if __name__=="__main__":
    register()
