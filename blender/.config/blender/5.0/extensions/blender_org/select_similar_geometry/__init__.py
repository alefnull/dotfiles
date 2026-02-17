bl_info = {
    "name": "Select Similar Geometry (by Percentage)",
    "author": "Juan Romero",
    "version": (1, 3, 0),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Select > Select Similar Geometry",
    "description": "Selects objects whose geometry matches the active one above a given percentage",
    "category": "Object",
}

import bpy
from mathutils import kdtree


def get_world_vertices(obj):
    """Return the list of vertex coordinates in world space."""
    m = obj.matrix_world
    return [m @ v.co for v in obj.data.vertices]


def build_kdtree(verts):
    """Build a KDTree from a list of vectors."""
    tree = kdtree.KDTree(len(verts))
    for i, co in enumerate(verts):
        tree.insert(co, i)
    tree.balance()
    return tree


def count_matches_from_ref_tree(ref_tree, target_verts, tol, ref_count, min_matches_required=None):
    """
    Count how many vertices in target_verts have a matching vertex in the
    reference tree within tolerance tol. Each reference vertex can only be
    matched once.

    Optionally uses an early-exit if min_matches_required is provided.
    """
    used_ref = set()
    matches = 0

    # Early-exit optimisation: if even matching every remaining vertex
    # cannot reach min_matches_required, stop.
    for i, co in enumerate(target_verts):
        _, ref_idx, dist = ref_tree.find(co)
        if ref_idx is not None and dist <= tol and ref_idx not in used_ref:
            matches += 1
            used_ref.add(ref_idx)
            if matches == ref_count:  # can't match more than reference count
                break

        if min_matches_required is not None:
            remaining = len(target_verts) - (i + 1)
            if matches + remaining < min_matches_required:
                break

    return matches


class OBJECT_OT_select_similar_geometry(bpy.types.Operator):
    """Select objects whose geometry is similar to the active object based on a minimum match percentage."""
    bl_idname = "object.select_similar_geometry"
    bl_label = "Select Similar Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    tol: bpy.props.FloatProperty(
        name="Tolerance",
        description="Distance threshold to consider two vertices as matching (in Blender units)",
        default=0.0001,
        min=0.0,
        max=1.0,
    )

    similarity_threshold: bpy.props.FloatProperty(
        name="Minimum Percentage",
        description="Minimum percentage of vertices from the active object that must be found in the other object",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    vertex_count_tolerance: bpy.props.FloatProperty(
        name="Vertex Count Tolerance",
        description=(
            "Allowed deviation in vertex count relative to the active object. "
            "For example, 0.2 means only objects with vertex counts within +/-20% "
            "of the active object's vertex count will be considered."
        ),
        default=0.2,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    use_world_space: bpy.props.BoolProperty(
        name="Use World Space",
        description="Compare vertices in world space (more strict when objects have different transforms)",
        default=False,
    )

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}
        if active_obj.type != 'MESH':
            self.report({'WARNING'}, "Active object is not a mesh")
            return {'CANCELLED'}

        ref_mesh = active_obj.data
        ref_vert_count = len(ref_mesh.vertices)
        if ref_vert_count == 0:
            self.report({'WARNING'}, "Active object has no vertices")
            return {'CANCELLED'}

        # Pre-calc allowed vertex count range
        low_count = int(ref_vert_count * (1.0 - self.vertex_count_tolerance))
        high_count = int(ref_vert_count * (1.0 + self.vertex_count_tolerance))

        # Build reference vertices list (local or world) and KDTree ONCE
        if self.use_world_space:
            ref_verts = get_world_vertices(active_obj)
        else:
            ref_verts = [v.co.copy() for v in ref_mesh.vertices]

        ref_tree = build_kdtree(ref_verts)

        # Minimum matches needed to reach similarity_threshold
        min_matches_required = int(ref_vert_count * self.similarity_threshold + 0.9999)

        # Deselect all mesh objects
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(False)
        active_obj.select_set(True)

        selected_count = 0

        # Iterate over all mesh objects
        for obj in context.scene.objects:
            if obj == active_obj or obj.type != 'MESH':
                continue

            # If they share the same mesh datablock, consider them identical
            if obj.data == ref_mesh:
                obj.select_set(True)
                selected_count += 1
                continue

            mesh = obj.data
            cand_vert_count = len(mesh.vertices)

            # Quick filter by vertex count range
            if cand_vert_count < low_count or cand_vert_count > high_count:
                continue

            # Get candidate vertices
            if self.use_world_space:
                verts = get_world_vertices(obj)
            else:
                verts = [v.co.copy() for v in mesh.vertices]

            if not verts:
                continue

            # Count matches using the pre-built reference KDTree
            matches = count_matches_from_ref_tree(
                ref_tree,
                verts,
                self.tol,
                ref_vert_count,
                min_matches_required=min_matches_required,
            )

            similarity = matches / ref_vert_count

            if similarity >= self.similarity_threshold:
                obj.select_set(True)
                selected_count += 1

        self.report(
            {'INFO'},
            f"Selection complete: {selected_count} similar object(s) found"
        )
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_select_similar_geometry.bl_idname, icon='MESH_CUBE')


def register():
    bpy.utils.register_class(OBJECT_OT_select_similar_geometry)
    bpy.types.VIEW3D_MT_select_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_select_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_select_similar_geometry)


if __name__ == "__main__":
    register()
