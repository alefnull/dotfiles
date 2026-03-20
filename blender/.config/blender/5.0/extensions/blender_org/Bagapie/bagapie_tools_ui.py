import bpy
from bpy.types import Menu, Operator
import bmesh
import os
from .utils import Get_addon_pref
from .bagapie_window_v2_op import exception_tool_window
from .bagapie_door_op import exception_tool_door
from pathlib import Path


###################################################################################
# PIE MENU
###################################################################################
class BAGAPIE_MT_pie_menu_tools(Menu):
    bl_label = "BagaPie Tools"
    bl_idname = "BAGAPIE_MT_pie_menu_tools"

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            objs = context.selected_objects
            # If no selection, use active obj
            if not objs and context.active_object:
                objs = [context.active_object]
            for obj in objs:
                bm = bmesh.from_edit_mesh(obj.data)
                verts_selected = any(v.select for v in bm.verts)
                edges_selected = any(e.select for e in bm.edges)
                faces_selected = any(f.select for f in bm.faces)
                return verts_selected or edges_selected or faces_selected
            return False
        return False

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        sections = {
            "Architecture": {
                "icon": "HOME",
                "tools": [
                    "BagaPieTools_Window Modern",
                    "BagaPieTools_Window Classic",
                    "BagaPieTools_Door Simple",
                    "BagaPieTools_Door Double",
                    "BagaPieTools_Cable Creator"
                ]
            },
            "Edit Mesh": {
                "icon": "EDGESEL",
                "tools": [
                    "BagaPieTools_Bool Through", 
                    "BagaPieTools_Tessellate",
                    "BagaPieTools_Insert Circle"
                ]
            },
            "Array": {
                "icon": "MOD_ARRAY",
                "tools": [
                    "BagaPieTools_Array Along Shape",
                    "BagaPieTools_Bolt Corner",
                ]
            },
            "Generate": {
                "icon": "RESTRICT_SELECT_OFF",
                "tools": [
                    "BagaPieTools_Face to Grid",
                    "BagaPieTools_Face to Paving",
                    "BagaPieTools_Face to Perforated_Grid",
                    "BagaPieTools_Face to Plank",
                ]
            }
        }

        prefs = bpy.context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries
        all_tools_present = False
        bagapie_pref = Get_addon_pref()

        for asset_library in asset_libraries:
            if asset_library.name != "BagaPie Modifier":
                continue

            library_path = Path(asset_library.path)
            target_blend_file = library_path / "BagaPie_Nodes_Tools.blend"

            if not target_blend_file.is_file():
                box = pie.box()
                box.label(text="Tool File missing !")
                box.label(text="Try to update BagaPie Parametric Library.")
                box.operator('bagapie.parametricpresets', icon = "ASSET_MANAGER", text = "Update BagaPie Parametric Library").tool_update=True

                all_tools_present = False
                if bagapie_pref.debug:
                    print("Is File : "+ target_blend_file.is_file())
                    print("Tool File Path : "+ target_blend_file)
                    print("Blender Version : "+ bpy.app.version)
                break
            else:
                all_tools_present = True

            # ONLY FOR DEBUG - IN CASE THE NODE TREE FILE HAS BEEN EDITED
            if bagapie_pref.debug:
                with bpy.data.libraries.load(str(target_blend_file), assets_only=True) as (file_contents, _):
                    # Check if all tools are present in BagaPie_Nodes_Tools.blend
                    for section in sections.values():
                        for tool in section["tools"]:
                            tool_tree_name = tool.replace(' ', '_')
                            if tool_tree_name not in file_contents.node_groups:
                                print("[" + tool_tree_name + "] is missing.")
        
        # User need to restart blender if the BagaPie Modifier library has just been created
        TEMP_FILE = os.path.join(bpy.app.tempdir, "bagapie_restart_flag.txt")
        if os.path.exists(TEMP_FILE):
            col = pie.column(align=False)
            col.scale_y = 2
            box = col.box()
            box.label(text="   Restart Blender   ")
        else:
            # Generate the pie menu if BagaPie_Nodes_Tools.blend is present
            if all_tools_present:
                for title, data in sections.items():
                    create_section(title, data, pie)
            else:
                col = pie.column(align=False)
                col_butt = col.column(align=False)
                col_butt.scale_y = 2
                col_butt.operator('bagapie.parametricpresets', icon = "ASSET_MANAGER", text = "SETUP TOOL !").tool_update=True
                box = col.box()
                box.label(text="Then restart Blender")
                box.label(text="(First time only)")


# CREATE PIE MENU SECTIONS
def create_section(title, data, pie):
    exception = [
        "BagaPieTools_Window Modern",
        "BagaPieTools_Window Classic",
        "BagaPieTools_Door Simple",
        "BagaPieTools_Door Double"
            ] #These tools need specific operation to perform

    col = pie.column(align=True)
    col.label(text=title, icon=data["icon"])
    pref = Get_addon_pref()
    for tool_name in data["tools"]:
        tool_prop_name = tool_name[13:].lower().replace(" ", "_")
        if getattr(pref, tool_prop_name, False): # tool visibility
            if tool_name in exception: # Custom Tools
                col.operator('bagapie.tools', text=tool_name[13:]).tool_name = tool_name
            else: # Generic Tools
                op = col.operator("geometry.execute_node_group", text=tool_name[13:])
                op.asset_library_type = 'CUSTOM'
                op.asset_library_identifier = "BagaPie Modifier"
                op.relative_asset_identifier = (f"BagaPie_Nodes_Tools.blend\\NodeTree\\{tool_name.replace(' ', '_')}")


###################################################################################
# EXECUTE EXCEPTION TOOLS - These tools need specific operation to perform
###################################################################################
class BAGAPIE_OP_execute_tool(Operator):
    """ Import and execute node group in edit mode """
    bl_idname = "bagapie.tools"
    bl_label = 'Tool'
    bl_options = {'REGISTER', 'UNDO'}
    
    tool_name: bpy.props.StringProperty(default="NONE", options={'HIDDEN'}) # type: ignore
    wall_thickness: bpy.props.FloatProperty(default=0.2, options={'HIDDEN'}) # type: ignore
    boolean_mode: bpy.props.BoolProperty(default=True, options={'HIDDEN'}) # type: ignore

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "wall_thickness")
        row= layout.row(align=True)
        row.prop(self, "boolean_mode", toggle=True, text = "Exact")
        row.prop(self, "boolean_mode", toggle=True, text = "Fast", invert_checkbox = True)

    def execute(self, context):
        ###################################################################################
        # WINDOW TOOL
        exception_window = ["BagaPieTools_Window Modern", "BagaPieTools_Window Classic"]
        if self.tool_name in exception_window:
            exception_tool_window(self, context, self.tool_name, self.wall_thickness, self.boolean_mode)
            return {'FINISHED'}

        ###################################################################################
        # DOOR TOOL
        exception_door = ["BagaPieTools_Door Simple", "BagaPieTools_Door Double"]
        if self.tool_name in exception_door:
            exception_tool_door(self, context, self.tool_name, self.wall_thickness, self.boolean_mode)
            return {'FINISHED'}
        
        return {'FINISHED'}


classes = [
    BAGAPIE_MT_pie_menu_tools,
    BAGAPIE_OP_execute_tool,
]