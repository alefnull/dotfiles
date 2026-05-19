"""
F-Curve helpers focused on camera rotation channels.

- _remove_non_rotation_fcurves(): prunes non-rotation curves from an Action.
- _rot_fcurves(): fetches rotation_euler fcurves (X/Y/Z) and the source Action.

"""

import bpy


class _FCurvesProxy:
    """Lightweight wrapper to present a unified fcurves API across Blender 4.x/5.x."""

    def __init__(self, bags):
        self._bags = tuple(bags)

    # iteration / truthiness -------------------------------------------------
    def __iter__(self):
        for bag in self._bags:
            for fcu in bag:
                yield fcu

    def __len__(self):
        return sum(len(bag) for bag in self._bags)

    def __bool__(self):
        return any(True for _ in self.__iter__())

    # methods ---------------------------------------------------------------
    def find(self, data_path, index=None):
        for bag in self._bags:
            try:
                fc = bag.find(data_path, index=index if index is not None else -1)
            except TypeError:
                try:
                    fc = bag.find(data_path)
                except Exception:
                    fc = None
            if fc:
                return fc
        return None

    def new(self, data_path, index=0, **kwargs):
        bag = self._bags[0] if self._bags else None
        if not bag:
            return None
        try:
            return bag.new(data_path=data_path, index=index, **kwargs)
        except TypeError:
            return bag.new(data_path=data_path, index=index)

    def remove(self, fcurve):
        for bag in self._bags:
            try:
                bag.remove(fcurve)
                return
            except Exception:
                continue

    def clear(self):
        for bag in self._bags:
            try:
                bag.clear()
            except Exception:
                continue


def _owner_id_type(owner):
    try:
        return owner.id_type
    except Exception:
        pass
    try:
        return owner.bl_rna.identifier.upper()
    except Exception:
        return "OBJECT"


def _ensure_slot(action, owner):
    slots = getattr(action, "slots", None)
    if not slots:
        print(f"DEBUG: No slots in action {action.name}")
        return None
    target_type = _owner_id_type(owner) if owner else "OBJECT"
    
    # 1. Try to find existing compatible slot
    try:
        for s in slots:
            if getattr(s, "target_id_type", None) == target_type:
                return s
    except Exception as e:
        print(f"DEBUG: Error finding slot: {e}")

    # 2. Try to create new slot with correct type
    name = (getattr(owner, "name", "") or "Slot")
    try:
        print(f"DEBUG: Creating slot {name} of type {target_type}")
        return slots.new(target_type, name)
    except Exception as e:
        print(f"DEBUG: Failed to create slot {target_type}: {e}")

    # 3. Fallback: Try to create generic OBJECT slot
    if target_type != "OBJECT":
        try:
            print(f"DEBUG: Creating fallback OBJECT slot")
            return slots.new("OBJECT", name)
        except Exception as e:
            print(f"DEBUG: Failed to create fallback slot: {e}")

    # 4. Last resort: return any existing slot
    try:
        return slots[0]
    except Exception:
        return None


def _gather_channelbag_collections(action):
    bags = []
    layers = getattr(action, "layers", None)
    if not layers:
        return bags
    try:
        layer_iter = list(layers)
    except Exception:
        layer_iter = []
    active_layer = getattr(layers, "active", None) or (layer_iter[0] if layer_iter else None)
    for layer in ([active_layer] if active_layer else []) + [l for l in layer_iter if l != active_layer]:
        strips = getattr(layer, "strips", None)
        if not strips:
            continue
        try:
            strip_iter = list(strips)
        except Exception:
            strip_iter = []
        active_strip = getattr(strips, "active", None) or (strip_iter[0] if strip_iter else None)
        for strip in ([active_strip] if active_strip else []) + [s for s in strip_iter if s != active_strip]:
            cbs = getattr(strip, "channelbags", None)
            if not cbs:
                continue
            try:
                cb_iter = list(cbs)
            except Exception:
                cb_iter = []
            active_cb = getattr(cbs, "active", None) or (cb_iter[0] if cb_iter else None)
            for cb in ([active_cb] if active_cb else []) + [c for c in cb_iter if c != active_cb]:
                fc = getattr(cb, "fcurves", None)
                if fc:
                    bags.append(fc)
    return bags


def _ensure_channelbag(action, owner):
    layers = getattr(action, "layers", None)
    if not layers:
        print("DEBUG: No layers collection")
        return None
    
    # Ensure layer
    layer = getattr(layers, "active", None)
    if not layer:
        try:
            layer = layers[0] if len(layers) > 0 else None
        except Exception:
            pass
    if not layer:
        try:
            layer = layers.new("Layer")
        except Exception as e:
            print(f"DEBUG: Failed to create layer: {e}")
            return None

    # Ensure strip
    strips = getattr(layer, "strips", None)
    if not strips:
        print("DEBUG: No strips collection")
        return None
        
    strip = getattr(strips, "active", None)
    if not strip:
        try:
            strip = strips[0] if len(strips) > 0 else None
        except Exception:
            pass
    if not strip:
        try:
            strip = strips.new(type='KEYFRAME')
        except Exception as e:
            print(f"DEBUG: Failed to create strip: {e}")
            return None

    cbags = getattr(strip, "channelbags", None)
    if not cbags:
        print("DEBUG: No channelbags collection")
        return None

    slot = _ensure_slot(action, owner)
    if not slot:
        print("DEBUG: _ensure_slot returned None")

    # Try to find existing bag for slot
    if slot:
        try:
            for cb in cbags:
                if getattr(cb, "slot", None) == slot:
                    return cb
        except Exception:
            pass

    # Create new bag for slot
    if slot:
        try:
            print(f"DEBUG: Creating channelbag for slot {slot.name}")
            return cbags.new(slot)
        except Exception as e:
            print(f"DEBUG: Failed to create channelbag: {e}")

    # Fallback: return first bag if exists
    try:
        return cbags[0]
    except Exception as e:
        print(f"DEBUG: Fallback cbags[0] failed: {e}")
        return None


def action_fcurves(action, owner=None, *, create=False):
    """Return an fcurves collection (legacy) or a proxy for layered actions."""
    if not action:
        return None

    fc = getattr(action, "fcurves", None)
    if fc is not None:
        return fc

    bags = _gather_channelbag_collections(action)
    if not bags and create:
        cb = _ensure_channelbag(action, owner)
        if cb and getattr(cb, "fcurves", None):
            bags = [cb.fcurves]

    if not bags:
        return _FCurvesProxy(())
    if len(bags) == 1:
        return bags[0]
    return _FCurvesProxy(bags)


def _remove_non_rotation_fcurves(obj):
    """Keep only rotation channels on the object action."""
    ad = getattr(obj, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return
    fcurves = action_fcurves(act, owner=obj)
    for fcu in list(fcurves):
        dp = fcu.data_path or ""
        if not (dp.startswith("rotation_euler") or dp.startswith("rotation_quaternion")):
            try:
                fcurves.remove(fcu)
            except Exception:
                pass


def _rot_fcurves(cam):
    ad = getattr(cam, "animation_data", None)
    act = ad.action if (ad and ad.action) else None
    if not act:
        return [], None
    fcurves = action_fcurves(act, owner=cam)
    found = []
    for i in (0, 1, 2):
        fcu = fcurves.find("rotation_euler", index=i)
        if fcu:
            found.append(fcu)
    return found, act
