import os
import bpy
import bpy.utils.previews
class Icon:
    icons = None

    @classmethod
    def register_icons(cls):
        if cls.icons is None:
            plugin_folder = os.path.dirname(__file__)
            path = os.path.join(plugin_folder, "icons")
            icons = bpy.utils.previews.new()
            for i in sorted(os.listdir(path)):
                if i.endswith(".png"):
                    iconname = i[:-4]
                    filepath = os.path.join(path, i)
                    icons.load(iconname, filepath, "IMAGE")
            cls.icons = icons

    @classmethod
    def unregister_icons(cls):
        try:
            bpy.utils.previews.remove(cls.icons)
            cls.icons = None
        except Exception as e:
            print(f"Unregistration failed: {e}")

    @classmethod
    def get_icon(cls, name):
        if cls.icons and name in cls.icons:
            return cls.icons[name].icon_id
        else:
            return 3
