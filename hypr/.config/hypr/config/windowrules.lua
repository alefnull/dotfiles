-- windowrules.lua
-- Window rules, layer rules, and workspace rules

-- Float essential dialogs
hl.window_rule({ match = { class = "^(org.pulseaudio.pavucontrol)" }, float = true, size = {960, 480} })
hl.window_rule({ match = { title = "^(Picture in picture)$" }, float = true })
hl.window_rule({ match = { title = "^(Save File)$" }, float = true, size = {1200, 800} })
hl.window_rule({ match = { class = "^(zen)$", title = "^(Save As - .*)$" }, float = true, size = {1200, 800} })
hl.window_rule({ match = { title = "^(Open File)$" }, float = true, size = {1200, 800} })
hl.window_rule({ match = { title = "^(Blender File View)$" }, float = true, size = {1200, 800} })
hl.window_rule({ match = { title = "^(Blender Render)$" }, float = true, size = {1920, 1080} })
hl.window_rule({ match = { class = "^(blueman-manager)$" }, float = true })
hl.window_rule({ match = { class = "^(xdg-desktop-portal-gtk|xdg-desktop-portal-kde|xdg-desktop-portal-hyprland)(.*)$" }, float = true })
hl.window_rule({ match = { class = "^(polkit-gnome-authentication-agent-1|hyprpolkitagent|org.org.kde.polkit-kde-authentication-agent-1)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(Steam - Self Updater)$" }, float = true })
hl.window_rule({ match = { class = "^(waypaper)$" }, float = true, size = {1280, 880} })
hl.window_rule({ match = { class = "^(qt-sudo)$" }, float = true, size = {960, 480} })
hl.window_rule({ match = { class = "^(swayimg)$" }, float = true })
hl.window_rule({ match = { class = "(clipse)" }, float = true, size = {1200, 600} })

-- Picture-in-Picture: float + pin + reposition
hl.window_rule({
    match = { title = "^(Picture-in-Picture)$" },
    float = true, pin = true,
    size = {960, 540},
    move = {"2560-window_w", "1600-window_h"},
})

-- Media / floating utilities
hl.window_rule({
    match = { title = "^(imv|mpv|danmufloat|termfloat|nemo|ncmpcpp)$" },
    float = true,
    move = {"monitor_w*0.25", "-"},
    size = {960, 540},
})

-- Pin danmufloat on top
hl.window_rule({ match = { title = "^(danmufloat)$" }, pin = true })

-- Prism Launcher
hl.window_rule({ match = { title = "^(.* — Prism Launcher 9.4)" }, float = true, size = {1920, 1080} })

-- Firefox: no blur for performance
hl.window_rule({ match = { class = "^(org.mozilla.firefox)$" }, no_blur = true })

-- Layer rules
hl.layer_rule({ match = { namespace = "logout_dialog" }, animation = "slide top" })
hl.layer_rule({ match = { namespace = "waybar" }, animation = "slide down" })
hl.layer_rule({ match = { namespace = "wallpaper" }, animation = "fade 50%" })

-- Workspace rules
hl.workspace_rule({ workspace = "special:scratchpad", gaps_in = 0, gaps_out = 0, on_created_empty = terminal })
