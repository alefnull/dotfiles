"""
General helpers for tagging, timeline management, and key insertion.

- tag_autocam() / find_ac_curve(): tag objects with the owning rig curve and resolve it later.
- _extend_timeline(): auto-extend playback range; records matrices during fly-record op.
- _insert_key(): thin wrapper for keyframe_insert.

"""


import bpy


# RIG TAGGING HELPERS

def tag_autocam(obj, curve):
    obj.autocam.curve = curve
    if obj is curve:
        curve.autocam.rig_built = False


def find_ac_curve(obj):
    if not obj:
        return None

    if obj.type == "CURVE" and obj.get("autocam_path"):
        return obj

    ac = getattr(obj, "autocam", None)
    return ac.curve if ac and ac.curve else None


# ADDITIONAL HELPERS

def _extend_timeline(scene):
    cam = scene.camera
    if not cam:
        return

    f = scene.frame_current
    # Recording is handled in the modal operator now.
    # Just ensure we don't run out of frames.

    if f >= scene.frame_end - 1:
        scene.frame_end += 10


def _insert_key(obj, path, frame):
    obj.keyframe_insert(
        data_path=path,
        frame=frame,
    )


__all__ = ("tag_autocam", "find_ac_curve", "_extend_timeline", "_insert_key")
