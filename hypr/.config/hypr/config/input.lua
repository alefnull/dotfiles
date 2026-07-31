-- input.lua
-- Input, keyboard, cursor settings

hl.config({
  input = {
    float_switch_override_focus = 2,
    follow_mouse = 1,
    kb_layout = "us",
    kb_model = "pc102",
    numlock_by_default = true,
  },
  cursor = {
    no_warps = true,
  },
})

hl.on("hyprland.start", function()
  hl.exec_cmd("setxkbmap -model pc105 -layout us -option grp:shifts_toggle")
end)
