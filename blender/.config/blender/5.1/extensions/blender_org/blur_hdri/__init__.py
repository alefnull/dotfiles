import bpy
from bpy.props import FloatProperty
from bpy.types import Operator
from PIL import Image, ImageFilter
import os
import numpy as np
import OpenEXR, Imath

# --- Operator ---
class NODE_OT_blur_env_image(Operator):
    bl_idname = "node.blur_env_image"
    bl_label = "Blur Image Node"
    bl_options = {"REGISTER", "UNDO"}

    radius: FloatProperty(
        name="Blur Radius",
        description="Radius for Gaussian Blur",
        default=5.0,
        min=0.1,
        max=100.0,
    )

    def execute(self, context):
        # --- Get active node tree ---
        node_tree = None
        space = context.space_data
        if space and hasattr(space, "node_tree") and space.node_tree:
            node_tree = space.node_tree
        elif (
            context.object
            and context.object.active_material
            and context.object.active_material.use_nodes
        ):
            node_tree = context.object.active_material.node_tree
        elif context.scene.world and context.scene.world.node_tree:
            node_tree = context.scene.world.node_tree

        if not node_tree:
            self.report({"ERROR"}, "No node tree found (material or world).")
            return {"CANCELLED"}

        nodes = node_tree.nodes
        selected_nodes = [n for n in nodes if n.select]
        if not selected_nodes:
            self.report({"ERROR"}, "No node selected.")
            return {"CANCELLED"}

        node = selected_nodes[0]
        if not (hasattr(node, "image") and node.image and node.image.filepath):
            self.report(
                {"ERROR"}, "Selected node is not an image node or has no image."
            )
            return {"CANCELLED"}

        img_path = bpy.path.abspath(node.image.filepath)
        base, ext = os.path.splitext(img_path)
        blurred_path = base + "_blurred" + ext

        try:
            if ext.lower() == ".exr":
                # --- Handle EXR ---
                blurred_img = self.process_exr(
                    img_path,
                    self.radius,
                    is_env=(node.bl_idname == "ShaderNodeTexEnvironment"),
                )

                # Save EXR with RGBA
                exr_file = OpenEXR.InputFile(img_path)
                header = exr_file.header()
                out_file = OpenEXR.OutputFile(blurred_path, header)
                out_file.writePixels(
                    {
                        "R": blurred_img[:, :, 0].astype(np.float32).tobytes(),
                        "G": blurred_img[:, :, 1].astype(np.float32).tobytes(),
                        "B": blurred_img[:, :, 2].astype(np.float32).tobytes(),
                        "A": blurred_img[:, :, 3].astype(np.float32).tobytes(),
                    }
                )
                out_file.close()

                new_image = bpy.data.images.load(blurred_path)

            else:
                # --- Handle non-EXR (JPEG, PNG, etc.) ---
                img = Image.open(img_path)
                if node.bl_idname == "ShaderNodeTexEnvironment":
                    img = self.pad_and_blur(img, self.radius)
                else:
                    img = img.filter(ImageFilter.GaussianBlur(radius=self.radius))
                img.save(blurred_path)
                new_image = bpy.data.images.load(blurred_path)

            # --- Create new node ---
            if node.bl_idname == "ShaderNodeTexImage":
                new_node = nodes.new(type="ShaderNodeTexImage")
            elif node.bl_idname == "ShaderNodeTexEnvironment":
                new_node = nodes.new(type="ShaderNodeTexEnvironment")
            else:
                self.report({"ERROR"}, "Unsupported node type.")
                return {"CANCELLED"}

            new_node.location = (node.location[0], node.location[1] - 300)
            new_node.image = new_image
            if hasattr(node, "color_space") and hasattr(new_node, "color_space"):
                new_node.color_space = node.color_space

        except Exception as e:
            self.report({"ERROR"}, f"Error: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}

    # --- Helper for EXR processing ---
    def process_exr(self, path, radius, is_env):
        exr_file = OpenEXR.InputFile(path)
        header = exr_file.header()
        dw = header["dataWindow"]
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)

        # Read RGB channels
        red = np.frombuffer(exr_file.channel("R", FLOAT), dtype=np.float32).reshape(
            (height, width)
        )
        green = np.frombuffer(exr_file.channel("G", FLOAT), dtype=np.float32).reshape(
            (height, width)
        )
        blue = np.frombuffer(exr_file.channel("B", FLOAT), dtype=np.float32).reshape(
            (height, width)
        )

        # Check if alpha exists
        if "A" in header["channels"]:
            alpha = np.frombuffer(
                exr_file.channel("A", FLOAT), dtype=np.float32
            ).reshape((height, width))
        else:
            alpha = np.ones((height, width), dtype=np.float32)

        img = np.stack([red, green, blue, alpha], axis=2)

        # Convert to 8-bit for Pillow
        img_uint8 = np.clip(img, 0, 1) * 255
        img_uint8 = img_uint8.astype(np.uint8)

        if is_env:
            pad = int(radius * 2)
            left = img_uint8[:, -pad:]
            right = img_uint8[:, :pad]
            img_uint8 = np.hstack([left, img_uint8, right])

        # Blur with Pillow
        pil_img = Image.fromarray(img_uint8)
        blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))
        blurred_np = np.array(blurred)

        if is_env:
            blurred_np = blurred_np[:, pad:-pad]

        # Convert back to float [0,1]
        return blurred_np.astype(np.float32) / 255.0

    # --- Helper for non-EXR env textures ---
    def pad_and_blur(self, img, radius):
        arr = np.array(img)
        pad = int(radius * 2)
        left = arr[:, -pad:]
        right = arr[:, :pad]
        arr = np.hstack([left, arr, right])
        pil_img = Image.fromarray(arr)
        blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))
        blurred_arr = np.array(blurred)[:, pad:-pad]
        return Image.fromarray(blurred_arr)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# --- Right-click Context Menu Integration ---
def draw_blur_menu(self, context):
    selected_nodes = [n for n in context.space_data.node_tree.nodes if n.select]
    if not selected_nodes:
        return

    node = selected_nodes[0]
    if node.bl_idname in {"ShaderNodeTexImage", "ShaderNodeTexEnvironment"}:
        self.layout.separator()
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"  # <-- ensures popup dialog appears
        layout.operator(NODE_OT_blur_env_image.bl_idname, text="Blur...", icon="IMAGE")


def register():
    bpy.utils.register_class(NODE_OT_blur_env_image)
    bpy.types.NODE_MT_context_menu.append(draw_blur_menu)


def unregister():
    bpy.utils.unregister_class(NODE_OT_blur_env_image)
    bpy.types.NODE_MT_context_menu.remove(draw_blur_menu)
