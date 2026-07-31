-- variables.lua
-- General config sections, workspace rules, gestures

local wc = require("config.wallust-colors")

hl.config({
   general = {
      gaps_in = 0,
      gaps_out = 0,
      border_size = 1,
      col = {
         inactive_border = wc.color0,
         active_border = wc.color1,
         nogroup_border = wc.color0,
         nogroup_border_active = wc.color15,
      },
      layout = "scrolling",
      snap = { enabled = true },
   },
   misc = {
      background_color = wc.color0,
      col = { splash = wc.color1 },
      disable_hyprland_logo = true,
      enable_swallow = true,
      focus_on_activate = true,
      font_family = "\"Fira Sans\"",
      splash_font_family = "\"Fira Sans\"",
      swallow_regex = "^(cachy-browser|firefox|nautilus|nemo|thunar|btrfs-assistant.)$",
      vrr = 0,
   },
   render = {
      direct_scanout = true,
   },
   group = {
      col = {
         border_active = wc.color1,
         border_inactive = wc.color0,
         border_locked_active = wc.color1,
         border_locked_inactive = wc.color0,
      },
      groupbar = {
         col = {
            active = wc.color1,
            inactive = wc.color0,
            locked_active = wc.color1,
            locked_inactive = wc.color0,
         },
         font_family = "\"JetBrainsMono Nerd Font\"",
         text_color = wc.foreground,
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

-- Old gestures block: workspace_swipe_distance/min_speed/create_new
-- Replaced by hl.gesture() — distance/speed/etc are now internal
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
