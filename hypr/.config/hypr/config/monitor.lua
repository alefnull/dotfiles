-- monitor.lua
-- Monitor configuration and XWayland settings

hl.env("GDK_SCALE", "1.20")

hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})

hl.monitor({ output = "eDP-1", mode = "2560x1600@240", position = "0x0", scale = 1 })
