# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import (
    StringProperty,
    EnumProperty,
)
from contextlib import contextmanager
from mathutils import (
    Vector,
)
import os
import numpy as np


# Margin for node bounds to ensure sockets and links are included.
node_margin = 30
# Node height isn't very accurate and needs more margin
node_extra_height = 30
# Margin for regions to hide unwanted UI parts (scrollbars, dividers, sidebar buttons).
region_margin = 20
# Image output settings
image_file_format = 'TIFF'
image_color_mode = 'RGB'
image_color_depth = '8'
image_tiff_codec = 'DEFLATE'

def compute_node_bounds(context, margin):
    """
    Compute the extend (in View2D space) of all nodes in a node tree.
    Returns the (min, max) vector of the node bounds.
    """    
    ui_scale = context.preferences.system.ui_scale
    space = context.space_data
    node_tree = space.edit_tree
    if not node_tree:
        return Vector((0.0, 0.0)), Vector((0.0, 0.0))
    bmin = Vector((1.0e8, 1.0e8))
    bmax = Vector((-1.0e8, -1.0e8))
    for node in node_tree.nodes:
        node_view_min = Vector((node.location_absolute[0], node.location_absolute[1] - node.height - node_extra_height)) * ui_scale
        node_view_max = Vector((node.location_absolute[0] + node.width, node.location_absolute[1])) * ui_scale

        bmin = Vector((min(bmin.x, node_view_min.x), min(bmin.y, node_view_min.y)))
        bmax = Vector((max(bmax.x, node_view_max.x), max(bmax.y, node_view_max.y)))
    return bmin - Vector((margin, margin)), bmax + Vector((margin, margin))


@contextmanager
def clean_node_window_region(context):
    """
    Creates a safe context for executing screenshots
    and ensures the region properties are reset afterwards.
    """
    try:
        # Remember image format settings
        img_settings = context.scene.render.image_settings
        file_format = img_settings.file_format
        color_mode = img_settings.color_mode
        color_depth = img_settings.color_depth
        tiff_codec = img_settings.tiff_codec
        # Set image format for screenshots
        img_settings.file_format = image_file_format
        img_settings.color_mode = image_color_mode
        img_settings.color_depth = image_color_depth
        img_settings.tiff_codec = image_tiff_codec

        space = context.space_data
        show_region_header = space.show_region_header
        show_context_path = space.overlay.show_context_path

        space.show_region_header = False
        space.overlay.show_context_path = False

        yield context

    finally:
        img_settings.file_format = file_format
        img_settings.color_mode = color_mode
        img_settings.color_depth = color_depth
        img_settings.tiff_codec = tiff_codec

        space.show_region_header = show_region_header
        space.overlay.show_context_path = show_context_path


class TileInfo:
    def __init__(self, context, region):
        v2d = region.view2d

        self.nodes_min, self.nodes_max = compute_node_bounds(context, node_margin)

        # Min/Max points of the region considered usable for screenshots.
        # The margin excludes some bits that can't be hidden (dividers, scrollbars, sidebar buttons).
        usable_region_min = Vector((region_margin, region_margin))
        usable_region_max = Vector((region.width - region_margin, region.height - region_margin))
        self.tile_margin = region_margin
        self.tile_size = (int(usable_region_max.x - usable_region_min.x), int(usable_region_max.y - usable_region_min.y))

        self.orig_view_min = Vector(v2d.region_to_view(usable_region_min.x, usable_region_min.y))
        self.orig_view_max = Vector(v2d.region_to_view(usable_region_max.x, usable_region_max.y))
        self.image_num = (int(self.nodes_size.x / self.view_size.x) + 1, int(self.nodes_size.y / self.view_size.y) + 1)
    
    @property
    def view_size(self):
        return self.orig_view_max - self.orig_view_min

    @property
    def nodes_size(self):
        return self.nodes_max - self.nodes_min

    @property
    def full_size(self):
        return (int(self.nodes_size[0]), int(self.nodes_size[1]))

    @property
    def tile_num(self):
        return self.image_num[0] * self.image_num[1]

    def tile_boxes(self, tile_index):
        in_start = (self.tile_margin, self.tile_margin)
        out_start = (tile_index[0] * self.tile_size[0], tile_index[1] * self.tile_size[1])
        tile_size_clamped = (
            min(out_start[0] + self.tile_size[0], self.full_size[0]) - out_start[0],
            min(out_start[1] + self.tile_size[1], self.full_size[1]) - out_start[1]
        )
        in_end = (in_start[0] + tile_size_clamped[0], in_start[1] + tile_size_clamped[1])
        out_end = (out_start[0] + tile_size_clamped[0], out_start[1] + tile_size_clamped[1])
        return (*in_start, *in_end), (*out_start, *out_end)


class NodeTreeScreenshotTiles(Operator):
    bl_idname = "node_tree_screenshot.screenshot_tiles"
    bl_label = "Node Tree Screenshot"
    bl_description = "Create screenshots of all visible areas of a node tree"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for saving the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    stitch_method: EnumProperty(
        name="Stitch Method",
        description="Method used for stitching tiles into a single image",
        items=[
            ('PIL', "PIL", "Use the Python Image Library. Requires the PIL module."),
            ('BLENDER', "Blender", "Use Blender image buffers"),
        ],
        default='PIL',
    )

    # Setting the area fullscreen invalidates the context.region.
    # Workaround is to simply search for the node editor window region.
    @staticmethod
    def find_node_editor_window_region(context):
        for region in context.area.regions:
            if region.type == 'WINDOW':
                return region

    def status_message(self, msg: str, allow_overwrite: bool=False):
        print(f"[Node Tree Screenshot] {msg}", end='\r' if allow_overwrite else '\n')

    @classmethod
    def poll(cls, context):
        space = context.space_data
        region = cls.find_node_editor_window_region(context)
        if space is None or space.type != 'NODE_EDITOR':
            return False
        if region is None:
            return False
        return True

    def invoke(self, context, event):
        import os
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "nodetree"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]
            self.filepath = blend_filepath + context.scene.render.file_extension

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def snap_node_editor(self, context, region, tile_info: TileInfo):
        context_override = context.copy()
        context_override["region"] = region
        render_settings = context.scene.render

        # View2D only offset relative panning, this utility provides a "goto" function.
        current_view_min = tile_info.orig_view_min
        def pan_to_view(view_min):
            nonlocal current_view_min
            delta = view_min - current_view_min
            with context.temp_override(**context_override):
                bpy.ops.view2d.pan(deltax=int(delta.x), deltay=int(delta.y))
            current_view_min = view_min

        image_files = dict()
        for i in range(tile_info.image_num[0]):
            for j in range(tile_info.image_num[1]):
                tile_i = i * tile_info.image_num[1] + j
                self.status_message(f"Screenshot tile {tile_i + 1}/{tile_info.tile_num}", tile_i < tile_info.tile_num - 1)
                pan_to_view(tile_info.nodes_min + Vector((i, j)) * tile_info.view_size)

                tmp_filepath = os.path.join(bpy.app.tempdir, f"node_tree_screenshot_tile_{i}_{j}{render_settings.file_extension}")
                with context.temp_override(**context_override):
                    bpy.ops.screen.screenshot_area(filepath=tmp_filepath)
                image_files[(i, j)] = tmp_filepath

        # Reset view.
        pan_to_view(tile_info.orig_view_min)

        return image_files

    def stitch_images_numpy(self, context, tile_info: TileInfo, image_files):
        if not image_files:
            return

        # NOTE: NumPy pixel arrays are declared with shape (HEIGHT, WIDTH, CHANNELS)
        # This ensures correct column-first ordering without having to define
        # a custom (r,g,b,a) data type because the color components stay together.

        pixels_out = np.zeros((tile_info.full_size[1], tile_info.full_size[0], 4), dtype=float)
        
        for tile_i, (tile_index, tile_filepath) in enumerate(image_files.items()):
            tile_image = context.blend_data.images.load(tile_filepath)
            assert tile_image.channels == 4, "Tile images should have 4 channels"

            in_box, out_box = tile_info.tile_boxes(tile_index)
            self.status_message(f"Stitch tile {tile_i + 1}/{tile_info.tile_num}", tile_i < tile_info.tile_num - 1)

            pixels_flat = np.fromiter(tile_image.pixels, dtype=float, count=tile_image.size[0] * tile_image.size[1] * 4)
            pixels_in = np.reshape(pixels_flat, (tile_image.size[1], tile_image.size[0], 4))
            pixels_out[out_box[1]:out_box[3], out_box[0]:out_box[2], :] = pixels_in[in_box[1]:in_box[3], in_box[0]:in_box[2], :]

            context.blend_data.images.remove(tile_image)

        full_image = context.blend_data.images.new("node_tree_screenshot", tile_info.full_size[0], tile_info.full_size[1])
        assert full_image.channels == 4, "Output image should have 4 channels"
        self.status_message(f"Copy to output image")
        full_image.pixels = pixels_out.flatten().tolist()
        full_image.update()

        self.status_message(f"Save output image")
        full_image.save(filepath=self.filepath)
        context.blend_data.images.remove(full_image)

    def stitch_images_pil(self, context, tile_info: TileInfo, image_files):
        from PIL import Image

        if not image_files:
            return
        
        full_image = Image.new("RGB", tile_info.full_size)

        for tile_i, (tile_index, tile_filepath) in enumerate(image_files.items()):
            with Image.open(tile_filepath) as tile_image:
                in_box, out_box = tile_info.tile_boxes(tile_index)
                self.status_message(f"Stitch tile {tile_i + 1}/{tile_info.tile_num}", tile_i < tile_info.tile_num - 1)

                # Note: Pillow library uses upper-left corner as (0, 0), subtract Y coordinate from height!
                pil_in_box = (in_box[0], tile_image.height - in_box[3], in_box[2], tile_image.height - in_box[1])
                pil_out_box = (out_box[0], full_image.height - out_box[3], out_box[2], full_image.height - out_box[1])
                tile_cropped = tile_image.crop(pil_in_box)
                full_image.paste(tile_cropped, pil_out_box)

        image_settings = context.scene.render.image_settings
        # Maps the Blender render settings file format to PIL settings.
        pil_settings = {
            "JPEG": {"format": "JPEG", "quality": image_settings.quality},
            "JPEG2000": {"format": "JPEG2000"},
            "PNG": {"format": "PNG"},
            "WEBP": {"format": "WebP"},
            "TIFF": {"format": "TIFF"},
        }
        pil_format = pil_settings.get(image_settings.file_format, None)
        if pil_format is None:
            self.status_message(f"Image format {image_settings.file_format} unsupported")
            return

        self.status_message(f"Save output image")
        full_image.save(self.filepath, **pil_format)

    def execute(self, context):
        # The fullscreen context is missing region property,
        # this provides overrides for running operators.
        region = self.find_node_editor_window_region(context)
        context_override = context.copy()
        context_override["region"] = region

        with clean_node_window_region(context):
            with context.temp_override(**context_override):
                bpy.ops.view2d.reset()
            tile_info = TileInfo(context, region)

            image_files = self.snap_node_editor(context, region, tile_info)

        if self.stitch_method == 'PIL':
            self.stitch_images_pil(context, tile_info, image_files)
        elif self.stitch_method == 'BLENDER':
            self.stitch_images_numpy(context, tile_info, image_files)

        self.status_message(f"Done")
        return {'FINISHED'}


def draw_menu_item(self, context):
    layout = self.layout
    layout.operator(NodeTreeScreenshotTiles.bl_idname)


def register():
    from bpy.utils import register_class
    register_class(NodeTreeScreenshotTiles)

    bpy.types.NODE_MT_view.append(draw_menu_item)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(NodeTreeScreenshotTiles)

    bpy.types.NODE_MT_view.remove(draw_menu_item)
