import math
import bmesh
import heapq
from bpy_extras import view3d_utils
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree
from collections import defaultdict

def line_rotation(a,b):
    dir = (b-a).normalized()
    if dir == Vector([-1,0,0]):
        return Quaternion(Vector([0,1,0]), math.pi)
    else:
        return Vector([1,0,0]).rotation_difference(dir)

def line_factor(p, a, b, clamp=False):
    s = b - a
    w = p - a
    ps = w.dot(s)
    if ps <= 0 and clamp:
        return 0.0
    l2 = s.dot(s)
    if ps >= l2 and clamp:
        closest = 1.0
    else:
        closest = ps / l2
    return closest

def line_snap(p, a, b, clamp=False):
    return a + line_factor(p, a, b, clamp) * (b-a)

def edge_rotation(edge):
    return line_rotation(edge.verts[0].co, edge.verts[1].co)

def edge_factor(edge, p, clamp=False):
    return line_factor(p, edge.verts[0].co, edge.verts[1].co, clamp)

def edge_dir(edge):
    return edge.verts[1].co - edge.verts[0].co

def edge_snap(edge, p, clamp=False):
    return edge.verts[0].co + edge_factor(edge, p, clamp) * edge_dir(edge)

def edge_distance(edge, p, clamp=True):
    x = edge_snap(edge, p, clamp)
    return (x-p).length

def edge_distance_between(edge, a, b, clamp=False):
    af = edge_factor(edge, a, clamp)
    bf = edge_factor(edge, b, clamp)
    return abs(af-bf) * edge_dir(edge).length

def edge_between(a, b):
    for e in a.link_edges:
        if e.other_vert(a) == b:
            return e
    return None

def plane_snap(origin, normal, p):
    return p-normal*normal.dot(p-origin)

def mouse_position_3d(context, mouse_pos, point=Vector()):
    region = context.region
    region3D = context.space_data.region_3d
    return view3d_utils.region_2d_to_location_3d(region, region3D, mouse_pos, point)

def position_3d_mouse(context, pos):
    return view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, pos)

class FakeEdge:
    def __init__(self, a=Vector(), b=None):
        class FakeVert:
            def __init__(self, co):
                self.co = co
        if b is None:
            b = a+Vector([1,0,0])
        self.verts = [FakeVert(a), FakeVert(b)]

class MeshTools():
    def __init__(self, object):
        self.object = object
        self.mesh = None
        self.refresh()

    def refresh(self):
        if self.mesh is not None:
            self.mesh.free()
        if self.object.data.is_editmode:
            self.mesh = bmesh.from_edit_mesh(self.object.data)
        else:
            self.mesh = bmesh.new()
            self.mesh.from_mesh(self.object.data)
        self.mesh.faces.ensure_lookup_table()
        self.mesh.edges.ensure_lookup_table()
        self.from_local = self.object.matrix_world
        self.to_local = self.from_local.inverted_safe()
        self.kd = KDTree(len(self.mesh.faces))
        for i,f in enumerate(self.mesh.faces):
            self.kd.insert(f.calc_center_median(), i)
        self.kd.balance()

    def sync(self):
        if self.mesh is not None:
            bmesh.ops.recalc_face_normals(self.mesh, faces=self.mesh.faces)
            if self.mesh.is_wrapped:
                bmesh.update_edit_mesh(self.object.data)
            else:
                self.mesh.to_mesh(self.object.data)
                self.object.data.update()
            self.mesh.faces.ensure_lookup_table()
            self.mesh.edges.ensure_lookup_table()

    def free(self, sync=False):
        if self.mesh is not None:
            if sync:
                self.sync()
            self.mesh.free()
        self.mesh = None
        self.kd = None

    def from_mouse(self, context, mouse_pos):
        return self.to_local @ mouse_position_3d(context, mouse_pos)

    def closest_edge_view(self, context, mouse_pos):
        return self.closest_edge(self.from_mouse(context, mouse_pos))

    def closest_edge(self, point):
        f = self.kd.find(point)[1]
        if f is None:
            return None
        edges = self.mesh.faces[f].edges
        if len(edges) < 1:
            return None
        e = edges[0]
        d = edge_distance(e, point)
        for i in range(1, len(edges)):
            dt = edge_distance(edges[i], point)
            if dt < d:
                d = dt
                e = edges[i]
        p = edge_snap(e, point)
        return (e,d,p,f)

    def closest_connected_edge(self, e, point):
        f = edge_factor(e, point)
        dir = edge_dir(e).normalized()
        if f < 0:
            dir = -dir
        while (f < 0 or 1 < f):
            v = e.verts[0] if f < 0.5 else e.verts[1]
            mindist = math.inf
            ne = e
            for ec in v.link_edges:
                v2 = ec.other_vert(v)
                dirc = (v2.co-v.co).normalized()
                # Don't consider edges that bend away from our principal direction
                if dirc.dot(dir) <= 0.1:
                    continue
                dist = edge_distance(ec, point)
                if dist < mindist:
                    mindist = dist
                    ne = ec
            if ne == e:
                break
            e = ne
            f = edge_factor(e, point)
        return e

    def edge_path(self, start, end):
        ## KLUDGE: this is really terrible, but we're essentially doing a dijkstra
        visited = set()
        prev = {}
        queue = []
        dist = defaultdict(lambda: math.inf)
        dist[start] = 0.0
        class Vert:
            def __init__(self, v, dist=0.0):
                self.v = v
                self.dist = dist
            def __lt__(self, other):
                return self.dist < other.dist

        heapq.heappush(queue, Vert(start))
        while queue:
            u = heapq.heappop(queue)
            u = u.v
            visited.add(u)
            for e in u.link_edges:
                v = e.other_vert(u)
                if v in visited:
                    continue
                alt = dist[u] + (v.co-start.co).length
                if dist[v] > alt:
                    prev[v] = (u,e)
                    dist[v] = alt
                    heapq.heappush(queue, Vert(v, alt))
        edges = []
        u = end
        while u is not None:
            u = prev.get(u)
            if u is not None:
                (u,e) = u
                edges.append(e)
        return edges

    def select(self, thing):
        for face in self.mesh.faces:
            face.select = False
        for edge in self.mesh.edges:
            edge.select = False
        for vertex in self.mesh.verts:
            vertex.select = False
        if hasattr(thing, '__iter__'):
            for e in thing:
                e.select = True
        else:
            thing.select = True
        self.mesh.select_flush(True)

    def create_vertex(self, e, point):
        f = edge_factor(e, point)
        if (0 < f and f < 1):
            return bmesh.utils.edge_split(e, e.verts[0], f)[1]
        elif 0 == f:
            return e.verts[0]
        elif 1 == f:
            return e.verts[1]
        else:
            ## We are well outside the edge, so extrude out a new vertex.
            v = e.verts[0] if f < 0 else e.verts[1]
            v = bmesh.ops.extrude_vert_indiv(self.mesh, verts=[v])['verts'][0]
            v.co = point
            return v

    def create_rect(self, se, start, point, dissolve_verts=True):
        ## If we have no edge, create it from a base direction
        if se is None:
            c2 = edge_snap(FakeEdge(start), point)
            a = self.mesh.verts.new(start)
            b = self.mesh.verts.new(c2)
            se = self.mesh.edges.new([a,b])
        ## First handle the endpoints, create vertices as necessary
        start = self.create_vertex(se, start)
        ee = self.closest_connected_edge(se, point)
        end = self.create_vertex(ee, edge_snap(ee, point))
        if end == start:
            return None
        disp = point-end.co
        ## Now that we have the bounding vertices, perform the edge extrusion
        es = self.edge_path(start, end)
        data = bmesh.ops.extrude_edge_only(self.mesh, edges=es)['geom']
        verts = [ x for x in data if isinstance(x, bmesh.types.BMVert) ]
        verts.sort(key=lambda v : edge_factor(se, v.co))
        for v in verts:
            v.co = v.co+disp
        if 2 < len(verts) and dissolve_verts:
            ## Fuse away the inner vertices in the new edge that were created
            bmesh.ops.dissolve_verts(self.mesh, verts=verts[1:-1])
            verts = (verts[0], verts[-1])
            es = edge_between(verts[0],verts[1])
        else:
            es = self.edge_path(verts[0],verts[-1])
        return (verts,es)
