-- decorations.lua
-- Window decoration, blur, shadow, and opacity settings

hl.config({
  decoration = {
    active_opacity = 1,
    blur = {
      enabled = true,
      xray = false,
    },
    dim_inactive = false,
    dim_special = 0.2,
    dim_strength = 0.0,
    inactive_opacity = 1,
    rounding = 0,
    shadow = {
      color = "rgba(121212aa)",
      enabled = true,
      range = 16,
      render_power = 2,
    },
  },
})
