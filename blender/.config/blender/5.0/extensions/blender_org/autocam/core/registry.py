"""
AutoCam 2.x Registry (forward-compat)

Responsibilities:
- Keep an in-session set of active rig *curve* Objects (by pointer).
- Stamp brand-new rigs with durable metadata (UUID, roles, schema, version).
- Discover rigs in an open file by reading that metadata (name- and hierarchy-proof).
- Optional helpers to repair pointers or reassign a new ID after duplication.

This file is the single source of truth for rig identity & discovery going forward.

"""

from __future__ import annotations
import uuid
import bpy

# -----------------------------
# In-session active rig pointers
# -----------------------------

_active: set[int] = set()


def add(curve) -> None:
    """Track this curve (Object) as an active AutoCam rig curve."""
    try:
        _active.add(curve.as_pointer())
    except Exception:
        pass


def remove(curve) -> None:
    """Stop tracking this curve."""
    try:
        _active.discard(curve.as_pointer())
    except Exception:
        pass


def clear_all() -> None:
    """Clear the active registry completely (e.g., after deleting all rigs)."""
    _active.clear()


def resolve_all():
    """Return live Object instances for all active pointers that still exist."""
    if not _active:
        return []
    wanted = _active.copy()
    # Filter existing objects by pointer (safe & simple).
    return [o for o in bpy.data.objects if o.as_pointer() in wanted]


# ------------------------------------
# 2.x forward-compat: rig ID metadata
# ------------------------------------

# ID Prop keys (stable-do not rename between releases)
AC_KIND_KEY = "ac_kind"  # "autocam" on all stamped IDs
# "curve" | "dolly" | "rigcam" | "look" | "focus" | "collection"
AC_ROLE_KEY = "ac_role"
RIG_UUID_KEY = "ac_rig_uuid"  # same UUID on all parts of one rig
SCHEMA_KEY = "ac_schema"  # integer schema version (for future migrations)
VERSION_KEY = "ac_version"  # string like "2.0.0"

SCHEMA_VERSION = 1


def _uuid() -> str:
    return str(uuid.uuid4())


def _stamp(id_owner, rig_uuid: str, role: str, version_str: str) -> None:
    """Attach AutoCam identity metadata to any ID owner (Object/Collection)."""
    if not id_owner:
        return
    try:
        id_owner[AC_KIND_KEY] = "autocam"
        id_owner[AC_ROLE_KEY] = role
        id_owner[RIG_UUID_KEY] = rig_uuid
        id_owner[SCHEMA_KEY] = SCHEMA_VERSION
        id_owner[VERSION_KEY] = version_str
    except Exception:
        # Non-fatal: ID props may be disallowed on some owners.
        pass


def _is_part(id_owner) -> bool:
    try:
        return id_owner and id_owner.get(AC_KIND_KEY) == "autocam" and RIG_UUID_KEY in id_owner
    except Exception:
        return False


def _role_of(id_owner):
    try:
        return id_owner.get(AC_ROLE_KEY)
    except Exception:
        return None


def get_rig_uuid(id_owner) -> str | None:
    """Public helper: read a stamped rig UUID from any rig part."""
    try:
        return id_owner.get(RIG_UUID_KEY)
    except Exception:
        return None


# ------------------------------------
# Stamping & discovery
# ------------------------------------

def stamp_rig(curve, dolly, *, rigcam=None, look=None, focus=None, coll=None, version_str: str = "2.0.0") -> str:
    rig_uuid = _uuid()
    _stamp(curve, rig_uuid, "curve",       version_str)
    _stamp(dolly, rig_uuid, "dolly",       version_str)
    _stamp(rigcam, rig_uuid, "rigcam",     version_str)
    _stamp(look,   rig_uuid, "look",       version_str)
    _stamp(focus,  rig_uuid, "focus",      version_str)
    _stamp(coll,   rig_uuid, "collection", version_str)
    return rig_uuid


def detect_rigs_by_metadata():
    rigs = {}
    for o in bpy.data.objects:
        if _is_part(o):
            uid = get_rig_uuid(o)
            rigs.setdefault(uid, {})
            rigs[uid][_role_of(o)] = o
    for c in bpy.data.collections:
        if _is_part(c):
            uid = get_rig_uuid(c)
            rigs.setdefault(uid, {})
            rigs[uid]["collection"] = c
    return rigs


def seed_from_scene():
    import bpy
    _active.clear()
    rigs = detect_rigs_by_metadata()
    if not rigs:
        return
    for uid, parts in rigs.items():
        curve = parts.get("curve")
        if not curve:
            continue
        ac = getattr(curve, "autocam", None)
        if ac:
            ac.curve = curve
            ac.rig_built = True
            try:
                if not ac.dolly and parts.get("dolly"):
                    ac.dolly = parts["dolly"]
            except Exception:
                pass
            try:
                if not ac.rigcam and parts.get("rigcam"):
                    ac.rigcam = parts["rigcam"]
            except Exception:
                pass
        _active.add(curve.as_pointer())


# -------------------------------------------------
# Maintenance helpers
# -------------------------------------------------

def repair_links_for_curve(curve) -> bool:
    ac = getattr(curve, "autocam", None)
    if not ac or not _is_part(curve):
        return False
    uid = get_rig_uuid(curve)
    if not uid:
        return False
    parts = {}
    for o in bpy.data.objects:
        if _is_part(o) and get_rig_uuid(o) == uid:
            parts[_role_of(o)] = o
    changed = False
    if not ac.curve:
        ac.curve = curve
        changed = True
    if not ac.rig_built:
        ac.rig_built = True
        changed = True
    if parts.get("dolly") and not ac.dolly:
        ac.dolly = parts["dolly"]
        changed = True
    if parts.get("rigcam") and not ac.rigcam:
        ac.rigcam = parts["rigcam"]
        changed = True
    return changed


def assign_new_uuid_for_curve(curve, *, version_str: str = "2.0.0") -> str:
    old = get_rig_uuid(curve)
    new = _uuid()
    _stamp(curve, new, "curve", version_str)
    ac = getattr(curve, "autocam", None)
    if ac and ac.dolly:
        cand = {ac.dolly}
        for ch in ac.dolly.children:
            cand.add(ch)
            for ch2 in ch.children:
                cand.add(ch2)
        for o in cand:
            if _is_part(o) and get_rig_uuid(o) == old:
                _stamp(o, new, _role_of(o) or "unknown", version_str)
    return new
