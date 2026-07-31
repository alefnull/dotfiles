-- Environment variables
-- hl.env(NAME, VALUE, dbus_export) — third arg true == old envd

hl.env("AQ_DRM_DEVICES", "/dev/dri/card1:/dev/dri/card0")
hl.env("HYPRCURSOR_THEME", "Catppuccin Mocha Light", true)
hl.env("HYPRCURSOR_SIZE", "32", true)
hl.env("XCURSOR_THEME", "Catppuccin Mocha Light", true)
hl.env("XCURSOR_SIZE", "32", true)
hl.env("QT_CURSOR_THEME", "Catppuccin Mocha Light", true)
hl.env("QT_CURSOR_SIZE", "32", true)
hl.env("QT_QPA_PLATFORM", "wayland;xcb", true)
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct", true)
hl.env("QT_SCALE_FACTOR", "1.1", true)
hl.env("QS_ICON_THEME", "Papirus Dark", true)
