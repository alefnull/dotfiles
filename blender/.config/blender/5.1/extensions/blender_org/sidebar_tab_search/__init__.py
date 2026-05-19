# Sidebar Tab Search - Blender Add-on
# Copyright (C) 2025-2026 McKaa

bl_info = {
    "name": "Sidebar Tab Search",
    "author": "McKaa",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Header",
    "description": "Quick search sidebar tabs with favorites and history.",
    "category": "Interface",
}

import bpy
import importlib
import json
import os
import subprocess
import sys
import time

from bpy_extras.io_utils import ExportHelper, ImportHelper

# --- CONSTANTS ---

# Unique add-on identifier. Uses __package__ when installed as extension,
# falls back to __name__ when run as a standalone script.
ADDON_ID = __package__ or __name__

STORAGE_FILE = "sidebar_tab_search_settings.json"
MAX_HISTORY_SIZE = 50
MAX_SEARCH_RESULTS = 120
CACHE_LIFETIME = 2.0  # seconds

# --- GLOBAL STATE ---

_UNREGISTERING = False
_STORAGE_CACHE = {"favorites": [], "install_dates": {}, "history": [], "aliases": {}}
_TABS_CACHE = []
_TABS_LAST_REFRESH = 0.0
_REFRESH_TIMER = None


# --- PERSISTENCE ---

def get_storage_path():
    """Return the path to the JSON settings file, creating the directory if needed.

    Uses ``extension_path_user`` (Blender 4.2+) so the add-on works correctly
    on read-only "System" repositories.  Falls back to ``user_resource('CONFIG')``
    for older Blender versions.
    """
    try:
        config_dir = bpy.utils.extension_path_user(__package__, create=True)
    except (AttributeError, ValueError):
        # AttributeError: Blender < 4.2 (function does not exist)
        # ValueError: addon loaded outside the Extensions system (e.g. symlink)
        config_dir = os.path.join(
            bpy.utils.user_resource('CONFIG'), "sidebar_tab_search",
        )
        os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, STORAGE_FILE)


def load_storage():
    """Load persisted settings from disk into ``_STORAGE_CACHE``."""
    path = get_storage_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _STORAGE_CACHE.update(data)
                    _STORAGE_CACHE.setdefault("aliases", {})
        except Exception as e:
            print(f"Sidebar Tab Search: Load error: {e}")


def save_storage(force=False):
    """Write ``_STORAGE_CACHE`` to disk.

    Skipped when the add-on is mid-unregister unless *force* is ``True``.
    """
    if _UNREGISTERING and not force:
        return
    try:
        with open(get_storage_path(), 'w', encoding='utf-8') as f:
            json.dump(_STORAGE_CACHE, f, indent=4)
    except Exception as e:
        print(f"Sidebar Tab Search: Save error: {e}")


def safe_redraw_ui():
    """Re-register the popover panel so Blender picks up ``bl_ui_units_x`` changes.

    This is a workaround: Blender caches ``bl_ui_units_x`` at registration time.
    Re-registering the class forces the new width value to take effect.
    Reassigning ``window.screen`` first closes any transient popups/panels safely
    to prevent a crash if the popover is currently drawn.
    """
    global _REFRESH_TIMER
    _REFRESH_TIMER = None
    if _UNREGISTERING:
        return
    try:
        for window in bpy.context.window_manager.windows:
            if hasattr(window, "screen") and window.screen:
                window.screen = window.screen
        bpy.utils.unregister_class(SEARCHTABS_PT_popover)
        bpy.utils.register_class(SEARCHTABS_PT_popover)
    except Exception:
        pass


# --- STORAGE HELPERS ---

def get_alias(name):
    """Return the custom alias for *name*, or an empty string."""
    return _STORAGE_CACHE.get("aliases", {}).get(name, "")


def set_alias(name, val):
    """Set or remove a custom alias for *name*."""
    if val:
        _STORAGE_CACHE["aliases"][name] = val
    elif name in _STORAGE_CACHE["aliases"]:
        del _STORAGE_CACHE["aliases"][name]
    save_storage()


def is_favorite(name):
    """Return ``True`` if *name* is in the favorites list."""
    return name in _STORAGE_CACHE["favorites"]


def toggle_fav(name):
    """Add *name* to favorites if absent, otherwise remove it."""
    favs = _STORAGE_CACHE["favorites"]
    if name in favs:
        favs.remove(name)
    else:
        favs.append(name)
    save_storage()


def get_ctime(mod_name):
    """Return the cached creation-time of the file backing *mod_name*."""
    cache = _STORAGE_CACHE["install_dates"]
    if mod_name in cache:
        return cache[mod_name]
    ct = 0.0
    mod = sys.modules.get(mod_name.split('.')[0])
    if mod and hasattr(mod, '__file__') and mod.__file__:
        try:
            ct = os.path.getctime(mod.__file__)
        except OSError:
            pass
    cache[mod_name] = ct
    return ct


# --- CORE LOGIC ---

def get_all_tabs(context, force_refresh=False):
    """Collect all visible VIEW_3D sidebar tabs and panels.

    Results are cached for ``CACHE_LIFETIME`` seconds to avoid repeated
    traversal of ``Panel.__subclasses__()`` on every UI draw call.
    Each panel's ``poll()`` is evaluated to skip entries that are not available
    in the current context (e.g. edit-mode-only panels while in object mode).
    """
    global _TABS_LAST_REFRESH, _TABS_CACHE
    if _UNREGISTERING:
        return []

    now = time.time()
    if not force_refresh and _TABS_CACHE and (now - _TABS_LAST_REFRESH < CACHE_LIFETIME):
        return _TABS_CACHE

    entries = []
    seen = set()

    for p in bpy.types.Panel.__subclasses__():
        try:
            if (getattr(p, 'bl_space_type', None) != 'VIEW_3D'
                    or getattr(p, 'bl_region_type', None) != 'UI'):
                continue

            cat = str(getattr(p, 'bl_category', '')).strip()
            if not cat or cat == "Search":
                continue

            if hasattr(p, 'poll'):
                try:
                    if not p.poll(context):
                        continue
                except Exception:
                    continue

            label = str(getattr(p, 'bl_label', "")).strip()
            idname = getattr(p, "bl_idname", "") or p.__name__
            ct = get_ctime(p.__module__)

            # Register Category (Tab)
            if cat not in seen:
                alias = get_alias(cat)
                entries.append({
                    'search': f"{cat} {alias}".lower(),
                    'display': cat,
                    'cat': cat,
                    'label': cat,
                    'is_main': True,
                    'ctime': ct,
                    'type': 'TAB',
                    'idname': idname,
                    'alias': alias,
                })
                seen.add(cat)

            # Register Panel (Deduplicate via category + label)
            if label:
                ukey = f"P|{cat}|{label}"
                if ukey not in seen:
                    disp = f"{label} ({cat})" if label != cat else label
                    alias = get_alias(disp)
                    entries.append({
                        'search': f"{label} {cat} {alias}".lower(),
                        'display': disp,
                        'cat': cat,
                        'label': label,
                        'is_main': False,
                        'ctime': ct,
                        'type': 'PANEL',
                        'idname': idname,
                        'alias': alias,
                    })
                    seen.add(ukey)
        except Exception:
            continue

    _TABS_CACHE = entries
    _TABS_LAST_REFRESH = now
    return entries


def sort_entries(entries, context, prio_favs=True):
    """Sort *entries* in-place using user preferences.

    Sorting priority (highest first):
      1. Favorites (when *prio_favs* is ``True``)
      2. TABs before PANELs
      3. User-chosen method (Alphabetical / Date / Recent)

    A single ``sort()`` call with a composite key is used instead of
    multiple sequential sorts for clarity and minor performance gain.
    """
    if _UNREGISTERING:
        return []

    prefs = context.preferences.addons.get(ADDON_ID)
    sort_method = prefs.preferences.default_sort_method if prefs else 'ALPHABETICAL'
    descending = (prefs.preferences.sort_direction if prefs else 'ASCENDING') == 'DESCENDING'

    # Pre-build history rank map for 'RECENT' sort
    hist_rank = {}
    if sort_method == 'RECENT':
        hist_rank = {
            h.get("display_name", ""): i
            for i, h in enumerate(_STORAGE_CACHE["history"])
        }

    def sort_key(entry):
        # Tier 1: favorites first
        fav = 0 if (prio_favs and is_favorite(entry.get('display', ''))) else 1
        # Tier 2: TABs before PANELs
        typ = 0 if entry.get('type') == 'TAB' else 1
        # Tier 3: user-chosen method
        if sort_method == 'ALPHABETICAL':
            val = entry.get('display', '')
        elif sort_method == 'DATE':
            val = -entry.get('ctime', 0) if descending else entry.get('ctime', 0)
        elif sort_method == 'RECENT':
            val = hist_rank.get(entry['display'], 9999)
        else:
            val = entry.get('display', '')
        return (fav, typ, val)

    reverse = descending and sort_method == 'ALPHABETICAL'
    entries.sort(key=sort_key, reverse=reverse)
    return entries


# --- PROPERTIES ---

class SEARCHTABS_PG_history_item(bpy.types.PropertyGroup):
    """Single entry in the sidebar-switch history."""
    category: bpy.props.StringProperty()
    display_name: bpy.props.StringProperty()
    icon_name: bpy.props.StringProperty()
    panel_idname: bpy.props.StringProperty()
    panel_label: bpy.props.StringProperty()
    is_tab: bpy.props.BoolProperty()


def update_query_dynamic(self, context):
    """Trigger a UI redraw whenever the search query changes."""
    if _UNREGISTERING:
        return
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


class SEARCHTABS_PG_properties(bpy.types.PropertyGroup):
    """Scene-level properties for the search popover."""
    search_query: bpy.props.StringProperty(
        name="Search",
        default="",
        options={'TEXTEDIT_UPDATE'},
        update=update_query_dynamic,
    )
    history: bpy.props.CollectionProperty(type=SEARCHTABS_PG_history_item)


# --- OPERATORS ---

class SEARCHTABS_OT_switch_tab(bpy.types.Operator):
    """Switch the active sidebar tab and optionally highlight a panel."""
    bl_idname = "searchtabs.switch_tab"
    bl_label = "Switch Tab"
    bl_description = "Switch to the specified sidebar tab and panel"
    bl_options = {'REGISTER', 'INTERNAL'}

    category_name: bpy.props.StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    target_panel_label: bpy.props.StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    panel_label: bpy.props.StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    panel_idname: bpy.props.StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    icon_name: bpy.props.StringProperty(default="NODE", options={'SKIP_SAVE', 'HIDDEN'})
    is_tab: bpy.props.BoolProperty(options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        if properties.is_tab:
            return f"Switch to the '{properties.category_name}' tab"
        return (
            f"Switch to the '{properties.category_name}' tab"
            f" and find the '{properties.panel_label}' panel"
        )

    def execute(self, context):
        if _UNREGISTERING:
            return {'CANCELLED'}

        target_cat = str(self.category_name)
        target_id = str(self.panel_idname)
        target_label = str(self.panel_label)

        target_area = None
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    target_area = area
                    break
            if target_area:
                break

        if not target_area:
            return {'CANCELLED'}

        for space in target_area.spaces:
            if space.type == 'VIEW_3D':
                space.show_region_ui = True
                break

        def do_switch():
            if _UNREGISTERING:
                return
            reg = next((r for r in target_area.regions if r.type == 'UI'), None)
            if reg and hasattr(reg, "active_panel_category"):
                try:
                    reg.active_panel_category = target_cat
                    reg.tag_redraw()
                    target_area.tag_redraw()
                except Exception:
                    pass

        # Detect collapsed-to-tabs state and warn user with a clear popup
        reg = next((r for r in target_area.regions if r.type == 'UI'), None)
        if reg and reg.width <= 30:
            def draw_popup(self_inner, context_inner):
                layout = self_inner.layout
                layout.row().label(
                    text=f"Tab '{target_cat}' selected", icon='INFO'
                )
                layout.label(
                    text="Sidebar is collapsed — click any tab label to expand"
                )
            context.window_manager.popup_menu(
                draw_popup, title="Note", icon='NONE'
            )

        # Sequential switches over a few frames for maximum reliability in 5.0
        bpy.app.timers.register(do_switch, first_interval=0.01)
        bpy.app.timers.register(do_switch, first_interval=0.1)

        # --- Update history ---
        hist_coll = context.scene.searchtabs_props.history
        idx = next(
            (i for i, x in enumerate(hist_coll) if x.category == target_cat),
            -1,
        )
        if idx != -1:
            hist_coll.remove(idx)

        item = hist_coll.add()
        item.category = target_cat
        item.display_name = self.target_panel_label or target_cat
        item.icon_name = self.icon_name
        item.panel_idname = target_id
        item.panel_label = target_label
        item.is_tab = self.is_tab

        if len(hist_coll) > 1:
            hist_coll.move(len(hist_coll) - 1, 0)
        while len(hist_coll) > MAX_HISTORY_SIZE:
            hist_coll.remove(len(hist_coll) - 1)

        _STORAGE_CACHE["history"] = [
            {
                "category": h.category,
                "display_name": h.display_name,
                "icon_name": h.icon_name,
                "panel_idname": h.panel_idname,
                "panel_label": h.panel_label,
                "is_tab": h.is_tab,
            }
            for h in hist_coll
        ]
        save_storage()
        return {'FINISHED'}


class SEARCHTABS_OT_set_alias(bpy.types.Operator):
    """Set or edit a custom display name (alias) for a sidebar item."""
    bl_idname = "searchtabs.set_alias"
    bl_label = "Set Custom Alias"
    bl_description = "Set or edit a custom name for this sidebar item"
    bl_options = {'REGISTER', 'INTERNAL'}

    display_name: bpy.props.StringProperty()
    new_alias: bpy.props.StringProperty(name="Alias")

    def execute(self, context):
        set_alias(self.display_name, self.new_alias.strip())
        return {'FINISHED'}

    def invoke(self, context, event):
        self.new_alias = get_alias(self.display_name)
        return context.window_manager.invoke_props_dialog(self)


class SEARCHTABS_OT_remove_alias(bpy.types.Operator):
    """Remove a previously set custom alias."""
    bl_idname = "searchtabs.remove_alias"
    bl_label = "Remove Custom Alias"
    bl_description = "Remove the custom alias for this item and revert to its original name"
    bl_options = {'INTERNAL'}

    display_name: bpy.props.StringProperty()

    def execute(self, context):
        set_alias(self.display_name, "")
        return {'FINISHED'}


class SEARCHTABS_OT_export_favorites(bpy.types.Operator, ExportHelper):
    """Export the favorites list to a JSON file."""
    bl_idname = "searchtabs.export_favorites"
    bl_label = "Export Favorites"
    bl_description = "Save your favorite sidebar tabs and panels to a JSON file"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({"favorites": _STORAGE_CACHE["favorites"]}, f, indent=4)
            self.report(
                {'INFO'},
                f"Favorites exported to {os.path.basename(self.filepath)}",
            )
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {e}")
        return {'FINISHED'}


class SEARCHTABS_OT_import_favorites(bpy.types.Operator, ImportHelper):
    """Import favorites from a JSON file, merging with existing ones."""
    bl_idname = "searchtabs.import_favorites"
    bl_label = "Import Favorites"
    bl_description = "Import favorites from a JSON file and merge them with your current list"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "favorites" in data:
                    new_favs = data["favorites"]
                    added = 0
                    for fav in new_favs:
                        if fav not in _STORAGE_CACHE["favorites"]:
                            _STORAGE_CACHE["favorites"].append(fav)
                            added += 1
                    save_storage()
                    self.report({'INFO'}, f"Imported {added} new favorites")
                else:
                    self.report({'ERROR'}, "Invalid favorites file")
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {e}")
        return {'FINISHED'}


class SEARCHTABS_OT_toggle_favorite(bpy.types.Operator):
    """Toggle an item's favorite status."""
    bl_idname = "searchtabs.toggle_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Add or remove this item from your favorites list"
    bl_options = {'INTERNAL'}

    display_name: bpy.props.StringProperty()

    def execute(self, context):
        if _UNREGISTERING:
            return {'CANCELLED'}
        toggle_fav(self.display_name)
        return {'FINISHED'}


# --- UI HELPERS ---

def draw_entry_row(layout, entry):
    """Draw a single tab/panel entry row with a favorite toggle button."""
    display = entry['display']
    cat = entry['cat']
    icon = 'NODE' if entry['is_main'] else 'DOT'
    idname = entry.get('idname', "")
    label = entry.get('label', "")
    alias = entry.get('alias', "")
    is_tab = entry.get('type') == 'TAB'

    row = layout.row(align=True)
    label_text = f"{display} [{alias}]" if alias else display
    op = row.operator("searchtabs.switch_tab", text=label_text, icon=icon)
    op.category_name = cat
    op.target_panel_label = display
    op.panel_idname = idname
    op.panel_label = label
    op.icon_name = icon
    op.is_tab = is_tab

    is_fav = is_favorite(display)
    sub = row.row(align=True)
    if not is_fav:
        sub.active = False
    fav_op = sub.operator(
        "searchtabs.toggle_favorite",
        text="",
        icon='SOLO_ON' if is_fav else 'SOLO_OFF',
        emboss=False,
    )
    fav_op.display_name = display


class SEARCHTABS_PT_popover(bpy.types.Panel):
    """Main search popover panel shown in the 3D Viewport header."""
    bl_label = "Search Tabs"
    bl_idname = "SEARCHTABS_PT_popover"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 16

    def draw(self, context):
        if _UNREGISTERING:
            return
        layout = self.layout
        props = getattr(context.scene, "searchtabs_props", None)
        if not props:
            return

        prefs = context.preferences.addons.get(ADDON_ID)

        row = layout.row(align=True)
        if hasattr(row, "activate_init"):
            row.activate_init = True
        row.prop(props, "search_query", text="", icon='VIEWZOOM')

        raw_entries = get_all_tabs(context)
        if not raw_entries:
            layout.label(text="No tabs found.")
            return

        query = props.search_query.lower().strip()
        recent_limit = prefs.preferences.max_recent_items if prefs else 5

        col = layout.column(align=True)
        if len(query) >= 2:
            entries = sort_entries(raw_entries, context, prio_favs=True)
            cnt = 0
            for entry in entries:
                if query in entry.get('search', ''):
                    cnt += 1
                    if cnt > MAX_SEARCH_RESULTS:
                        break
                    draw_entry_row(col, entry)
            if cnt == 0:
                col.label(text="No results")
        elif len(query) == 1:
            col.label(text="Type 2+ chars...")
        else:
            # Default view: Favorites → Recent → Categories
            fav_entries = [e for e in raw_entries if is_favorite(e['display'])]
            if fav_entries:
                col.label(text="Favorites", icon='SOLO_ON')
                fav_entries.sort(key=lambda x: x['display'])
                for entry in fav_entries:
                    draw_entry_row(col, entry)

            hist = _STORAGE_CACHE.get("history", [])
            if hist:
                live_cats = {e['cat'] for e in raw_entries}
                valid_hist = [
                    h for h in hist
                    if isinstance(h, dict) and h.get('category') in live_cats
                ]
                if valid_hist:
                    col.label(text="Recent", icon='TIME')
                    for h in valid_hist[:recent_limit]:
                        hist_entry = {
                            'display': h.get('display_name', 'Unknown'),
                            'cat': h.get('category', ''),
                            'is_main': h.get('is_tab', False),
                            'idname': h.get('panel_idname', ''),
                            'label': h.get('panel_label', ''),
                            'type': 'TAB' if h.get('is_tab') else 'PANEL',
                        }
                        draw_entry_row(col, hist_entry)

            col.label(text="Categories", icon='FILE_FOLDER')
            main_entries = sort_entries(
                [x for x in raw_entries if x['is_main']],
                context,
                prio_favs=False,
            )
            for entry in main_entries:
                draw_entry_row(col, entry)


class SEARCHTABS_OT_call_popover(bpy.types.Operator):
    """Open the sidebar tab search popover."""
    bl_idname = "searchtabs.call_popover"
    bl_label = "Search Sidebar"
    bl_description = "Open the sidebar tab search popover menu"

    def execute(self, context):
        if _UNREGISTERING:
            return {'CANCELLED'}
        bpy.ops.wm.call_panel(name="SEARCHTABS_PT_popover")
        return {'FINISHED'}


class SEARCHTABS_OT_search_popup(bpy.types.Operator):
    """Open the Blender-native search popup with all sidebar tabs."""
    bl_idname = "searchtabs.search_popup"
    bl_label = "Search Sidebar Tab"
    bl_description = "Quickly search and jump to any sidebar tab or panel using a popup"
    bl_property = "search_enum"

    def build_enum(self, context):
        if _UNREGISTERING:
            return [("", "Shutting down...", "", 'ERROR', 0)]
        items = []
        for entry in sort_entries(get_all_tabs(context), context):
            uid = (
                f"{entry['cat']}|{entry['display']}"
                f"|{entry.get('idname', '')}|{entry.get('label', '')}"
                f"|NODE|{1 if entry['type'] == 'TAB' else 0}"
            )
            if entry['is_main']:
                item_label = entry['display']
            else:
                item_label = f"{entry.get('label', '')}  >  {entry['cat']}"
            items.append((
                uid,
                item_label,
                "",
                'NODE' if entry['is_main'] else 'DOT',
                len(items),
            ))
        return items if items else [("", "No Tags", "", 'ERROR', 0)]

    search_enum: bpy.props.EnumProperty(name="Tab", items=build_enum)

    def execute(self, context):
        if _UNREGISTERING:
            return {'CANCELLED'}
        if self.search_enum:
            parts = self.search_enum.split('|')
            if len(parts) >= 6:
                bpy.ops.searchtabs.switch_tab(
                    category_name=parts[0],
                    target_panel_label=parts[1],
                    panel_idname=parts[2],
                    panel_label=parts[3],
                    icon_name=parts[4],
                    is_tab=(parts[5] == "1"),
                )
        return {'FINISHED'}

    def invoke(self, context, event):
        if _UNREGISTERING:
            return {'CANCELLED'}
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


# --- PREFERENCES ---

class SEARCHTABS_AddonPreferences(bpy.types.AddonPreferences):
    """User-facing preferences for the Sidebar Tab Search add-on."""
    bl_idname = ADDON_ID

    max_recent_items: bpy.props.IntProperty(
        name="Max Recent Items", default=5, min=1, max=50,
    )

    def update_width(self, context):
        if _UNREGISTERING:
            return
        # Update class attribute immediately
        SEARCHTABS_PT_popover.bl_ui_units_x = self.popover_width

        # Debounced safe refresh to prevent crash during slider drag
        global _REFRESH_TIMER
        if _REFRESH_TIMER:
            try:
                bpy.app.timers.unregister(_REFRESH_TIMER)
            except Exception:
                pass

        _REFRESH_TIMER = safe_redraw_ui
        bpy.app.timers.register(_REFRESH_TIMER, first_interval=0.2)

    popover_width: bpy.props.IntProperty(
        name="Popover Width",
        description="Width of the search menu in UI units",
        default=16, min=10, max=40,
        update=update_width,
    )
    default_sort_method: bpy.props.EnumProperty(
        name="Sort Method",
        items=[
            ('ALPHABETICAL', "A-Z", ""),
            ('DATE', "Installation Date", ""),
            ('RECENT', "Recent", ""),
        ],
        default='ALPHABETICAL',
    )
    sort_direction: bpy.props.EnumProperty(
        name="Sort Direction",
        items=[
            ('ASCENDING', "Ascending", ""),
            ('DESCENDING', "Descending", ""),
        ],
        default='ASCENDING',
    )
    show_header_popup: bpy.props.BoolProperty(
        name="Show Popup Icon", default=True,
    )
    show_header_popover: bpy.props.BoolProperty(
        name="Show Popover Icon", default=True,
    )

    def draw(self, context):
        layout = self.layout

        # General Settings
        box = layout.box()
        box.label(text="General Settings", icon='SETTINGS')
        col = box.column()
        col.prop(self, "popover_width", text="Menu Width")
        col.prop(self, "max_recent_items", text="Recent Limit")

        col = box.column(align=True)
        col.label(text="Tab Sorting:")
        row = col.row(align=True)
        row.prop(self, "default_sort_method", text="")
        row.prop(self, "sort_direction", text="")

        # Keyboard Shortcuts
        box = layout.box()
        box.label(text="Keyboard Shortcuts", icon='KEYINGSET')
        col = box.column()
        wm = context.window_manager
        seen_ids = set()
        for kc in wm.keyconfigs:
            km = kc.keymaps.get('3D View')
            if not km:
                continue
            for kmi in km.keymap_items:
                if kmi.idname in {"searchtabs.search_popup", "searchtabs.call_popover"}:
                    if kmi.idname in seen_ids:
                        continue
                    seen_ids.add(kmi.idname)
                    row = col.row(align=True)
                    if kmi.idname == "searchtabs.search_popup":
                        row.label(text="Popup (F3)")
                    else:
                        row.label(text="Popover Menu")
                    row.prop(kmi, "type", text="", full_event=True)
                    op = row.operator(
                        "searchtabs.reset_keymap", text="", icon='X',
                    )
                    op.idname = kmi.idname
                    if kmi.idname == "searchtabs.search_popup":
                        row.prop(self, "show_header_popup", text="")
                    else:
                        row.prop(self, "show_header_popover", text="")

        # Favorites Backup
        box = layout.box()
        box.label(text="Favorites Backup", icon='DUPLICATE')
        row = box.row(align=True)
        row.operator("searchtabs.export_favorites", icon='EXPORT')
        row.operator("searchtabs.import_favorites", icon='IMPORT')


class SEARCHTABS_OT_reset_keymap(bpy.types.Operator):
    """Clear a keyboard shortcut assigned to this add-on."""
    bl_idname = "searchtabs.reset_keymap"
    bl_label = "Reset Shortcut"
    bl_description = "Clear this keyboard shortcut"
    bl_options = {'INTERNAL'}

    idname: bpy.props.StringProperty()

    def execute(self, context):
        wm = context.window_manager
        for kc in wm.keyconfigs:
            km = kc.keymaps.get('3D View')
            if not km:
                continue
            for kmi in km.keymap_items:
                if kmi.idname == self.idname:
                    kmi.type = 'NONE'
                    return {'FINISHED'}
        return {'CANCELLED'}


# --- CONTEXT MENU HELPERS ---

def find_addon_module(category, display_name, is_tab=False):
    """Find the add-on module name providing a given sidebar tab or panel.

    Returns an empty string for built-in Blender categories or when the
    owning module cannot be determined unambiguously.
    """
    SYSTEM_CATEGORIES = {"Item", "Tool", "View", "Edit", "Create"}
    if is_tab and category in SYSTEM_CATEGORIES:
        return ""

    if not is_tab:
        # Looking for a specific panel
        for p in bpy.types.Panel.__subclasses__():
            try:
                p_cat = getattr(p, 'bl_category', '')
                p_label = getattr(p, 'bl_label', '')
                disp = f"{p_label} ({p_cat})" if p_label != p_cat else p_label
                if p_cat == category and disp == display_name:
                    parts = p.__module__.split(".")
                    pkg = parts[0] if parts[0] != "bl_ext" else ".".join(parts[:3])
                    if pkg not in {"bpy", "bl_ui"}:
                        return pkg
            except Exception:
                continue
        return ""

    # Tab (category) — find the unique owning add-on module
    modules = set()
    system_found = False
    for p in bpy.types.Panel.__subclasses__():
        try:
            if getattr(p, 'bl_category', '') == category:
                parts = p.__module__.split(".")
                pkg = parts[0] if parts[0] != "bl_ext" else ".".join(parts[:3])
                if pkg in {"bpy", "bl_ui"}:
                    system_found = True
                else:
                    modules.add(pkg)
        except Exception:
            continue

    # Only return module if it's a unique addon tab (no system panels, single addon)
    if system_found or len(modules) > 1:
        return ""
    return next(iter(modules)) if modules else ""


class SEARCHTABS_OT_open_addon_prefs(bpy.types.Operator):
    """Open the owning add-on's preference page in Blender settings."""
    bl_idname = "searchtabs.open_addon_prefs"
    bl_label = "Open in Preferences"
    bl_description = "Open this add-on's settings in Blender Preferences"
    bl_options = {'INTERNAL'}

    module: bpy.props.StringProperty()

    def execute(self, context):
        if self.module:
            try:
                bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
                context.preferences.active_section = 'ADDONS'
                bpy.ops.preferences.addon_show(module=self.module)
            except Exception:
                pass
        return {'FINISHED'}


class SEARCHTABS_OT_open_addon_folder(bpy.types.Operator):
    """Open the add-on's directory in the system file manager."""
    bl_idname = "searchtabs.open_addon_folder"
    bl_label = "Open in Explorer"
    bl_description = "Open the folder containing this add-on's scripts"
    bl_options = {'INTERNAL'}

    module: bpy.props.StringProperty()

    def execute(self, context):
        if not self.module:
            return {'CANCELLED'}

        try:
            mod = sys.modules.get(self.module) or importlib.import_module(self.module)
            if not (mod and hasattr(mod, "__file__") and mod.__file__):
                return {'CANCELLED'}

            path = os.path.normpath(os.path.dirname(mod.__file__))

            if sys.platform == 'win32':
                subprocess.Popen(['explorer', path])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            print(f"Sidebar Tab Search: Could not open folder: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


# --- HEADER & CONTEXT MENU DRAW FUNCTIONS ---

def draw_header(self, context):
    """Append search icons to the 3D Viewport header."""
    if _UNREGISTERING:
        return
    layout = self.layout.row(align=True)
    prefs = context.preferences.addons.get(ADDON_ID)
    if not prefs:
        return
    if prefs.preferences.show_header_popup:
        layout.operator("searchtabs.search_popup", text="", icon='VIEWZOOM')
    if prefs.preferences.show_header_popover:
        layout.operator(
            "searchtabs.call_popover", text="", icon='DISCLOSURE_TRI_DOWN',
        )


def draw_context(self, context):
    """Populate the right-click context menu for search result buttons."""
    if _UNREGISTERING:
        return
    op = getattr(context, "button_operator", None)
    if not op or not (hasattr(op, "category_name") and hasattr(op, "target_panel_label")):
        return

    cat = op.category_name
    display = op.target_panel_label
    is_tab = getattr(op, "is_tab", False)

    mod = find_addon_module(cat, display, is_tab=is_tab)
    lay = self.layout

    lay.separator()
    fav_text = "Remove Favorite" if is_favorite(display) else "Add Favorite"
    fav_icon = 'SOLO_ON' if is_favorite(display) else 'SOLO_OFF'
    lay.operator(
        "searchtabs.toggle_favorite", text=fav_text, icon=fav_icon,
    ).display_name = display

    lay.separator()
    alias = get_alias(display)
    alias_text = "Edit Custom Alias" if alias else "Set Custom Alias"
    lay.operator(
        "searchtabs.set_alias", text=alias_text, icon='GREASEPENCIL',
    ).display_name = display
    if alias:
        lay.operator(
            "searchtabs.remove_alias", text="Remove Custom Alias", icon='X',
        ).display_name = display

    if mod:
        lay.separator()
        lay.operator(
            "searchtabs.open_addon_prefs", icon='PREFERENCES',
        ).module = mod
        lay.operator(
            "searchtabs.open_addon_folder", icon='FILE_FOLDER',
        ).module = mod


# --- REGISTRATION ---

classes = (
    SEARCHTABS_PG_history_item,
    SEARCHTABS_PG_properties,
    SEARCHTABS_OT_switch_tab,
    SEARCHTABS_OT_toggle_favorite,
    SEARCHTABS_OT_set_alias,
    SEARCHTABS_OT_remove_alias,
    SEARCHTABS_OT_export_favorites,
    SEARCHTABS_OT_import_favorites,
    SEARCHTABS_OT_open_addon_prefs,
    SEARCHTABS_OT_open_addon_folder,
    SEARCHTABS_OT_call_popover,
    SEARCHTABS_OT_search_popup,
    SEARCHTABS_PT_popover,
    SEARCHTABS_AddonPreferences,
    SEARCHTABS_OT_reset_keymap,
)

_KMS = []


def register():
    global _UNREGISTERING
    _UNREGISTERING = False
    load_storage()

    for cls in classes:
        bpy.utils.register_class(cls)

    # Initialize UI width from preferences
    prefs = bpy.context.preferences.addons.get(ADDON_ID)
    if prefs:
        SEARCHTABS_PT_popover.bl_ui_units_x = prefs.preferences.popover_width

    bpy.types.Scene.searchtabs_props = bpy.props.PointerProperty(
        type=SEARCHTABS_PG_properties,
    )
    bpy.types.VIEW3D_HT_header.append(draw_header)
    if hasattr(bpy.types, "WM_MT_button_context"):
        bpy.types.WM_MT_button_context.append(draw_context)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon or wm.keyconfigs.user
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        _KMS.append((
            km,
            km.keymap_items.new(
                "searchtabs.search_popup", 'T', 'PRESS', shift=True, alt=True,
            ),
        ))
        _KMS.append((
            km,
            km.keymap_items.new(
                "searchtabs.call_popover", 'T', 'PRESS',
                ctrl=True, shift=True, alt=True,
            ),
        ))


def unregister():
    global _UNREGISTERING
    save_storage(force=True)
    _UNREGISTERING = True

    # Force close active popovers to prevent crash when disabling addon with UI open
    try:
        if bpy.context and hasattr(bpy.context, "window") and bpy.context.window:
            bpy.context.window.screen = bpy.context.window.screen
    except Exception:
        pass

    for km, kmi in _KMS:
        km.keymap_items.remove(kmi)
    _KMS.clear()

    bpy.types.VIEW3D_HT_header.remove(draw_header)
    if hasattr(bpy.types, "WM_MT_button_context"):
        try:
            bpy.types.WM_MT_button_context.remove(draw_context)
        except Exception:
            pass

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    if hasattr(bpy.types.Scene, "searchtabs_props"):
        del bpy.types.Scene.searchtabs_props


if __name__ == "__main__":
    register()
