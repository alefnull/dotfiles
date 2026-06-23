require("wallust-colors")

hl.config({
    general = {
        border_size = 1,
        col.active_border = "$color1",
        col.inactive_border = "$color0",
        col.nogroup_border = "$color0",
        col.nogroup_border_active = "$color15",
        gaps_in = 0,
        gaps_out = 0,
        layout = "scrolling",
        snap = {
            enabled = true,
        },
    },
    misc = {
        background_color = "$color0",
        col.splash = "$color1",
        disable_hyprland_logo = true,
        enable_swallow = true,
        focus_on_activate = true,
        font_family = ""Fira Sans"",
        splash_font_family = ""Fira Sans"",
        swallow_regex = "^(cachy-browser|firefox|nautilus|nemo|thunar|btrfs-assistant.)$",
        vrr = 0,
    },
    render = {
        direct_scanout = true,
    },
    group = {
        col.border_active = "$color1",
        col.border_inactive = "$color0",
        col.border_locked_active = "$color1",
        col.border_locked_inactive = "$color0",
        groupbar = {
            col.active = "$color1",
            col.inactive = "$color0",
            col.locked_active = "$color1",
            col.locked_inactive = "$color0",
            font_family = ""JetBrainsMono Nerd Font"",
            text_color = "$foreground",
        },
    },
    dwindle = {
        preserve_split = true,
        special_scale_factor = 1,
    },
    master = {
        new_status = "master",
        special_scale_factor = 1,
    },
    scrolling = {
        column_width = 1.0,
        direction = "right",
        focus_fit_method = 0,
        follow_focus = true,
        follow_min_visible = 1.0,
        fullscreen_on_one_column = true,
    },
})

hl.workspace_rule({ workspace = "250" })
hl.workspace_rule({ workspace = "15" })
hl.workspace_rule({ workspace = "false" })
