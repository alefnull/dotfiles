-- hyprland.lua — Hyprland 0.55+ Lua config
-- Replaces the old hyprland.conf

mainMod = "SUPER"

-- Shared variables (globals so all modules can reference them)
require("config.defaults")

-- Environment variables
require("config.environment")

-- Monitor setup
require("config.monitor")

-- Input
require("config.input")

-- Colors (globals from wallust)
require("config.wallust-colors")

-- Decoration, look and feel
require("config.decorations")

-- General variables, sections, gestures
require("config.variables")

-- Animations
require("config.animations")

-- Window / layer / workspace rules
require("config.windowrules")

-- Keybindings
require("config.keybinds")

-- Autostart (hyprland.start event)
require("config.autostart")
