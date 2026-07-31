-- keybinds.lua
-- All keybindings, mouse bindings, and media keys
-- Depends on globals from config/defaults.lua (terminal, browser, etc.)

--------- Binds config ----------
hl.config({
   binds = {
      allow_workspace_cycles = true,
      workspace_back_and_forth = true,
      workspace_center_on = true,
      movefocus_cycles_fullscreen = true,
      window_direction_monitor_fallback = true,
   },
})

--------- Application launchers ----------
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal), { description = "Open terminal" })
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(filemanager), { description = "Open file manager" })
hl.bind(mainMod .. " + S", hl.dsp.exec_cmd(capturing), { description = "Region screenshot" })
hl.bind(mainMod .. " + CTRL + S", hl.dsp.exec_cmd(screencap), { description = "Full screenshot" })
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(discord), { description = "Open Discord" })
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd(wmenu), { description = "Application launcher" })
hl.bind(mainMod .. " + I", hl.dsp.exec_cmd(emojipicker), { description = "Emoji picker" })
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("fish -c 'touchtoggle'"), { description = "Toggle touchpad" })
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd(wallswitcher), { description = "Switch wallpaper" })
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(browser), { description = "Open browser" })

--------- Window management ----------
hl.bind(mainMod .. " + Q", hl.dsp.window.close(), { description = "Close window" })
hl.bind(mainMod .. " + SHIFT + M", hl.dsp.exec_cmd("loginctl terminate-user \"\""), { description = "Exit Hyprland" })
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }), { description = "Toggle float" })
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen(), { description = "Toggle fullscreen" })
hl.bind(mainMod .. " + Y", hl.dsp.window.pin(), { description = "Pin window" })

--------- Window focus (vim keys) ----------
hl.bind(mainMod .. " + h", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + l", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + k", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + j", hl.dsp.focus({ direction = "down" }))

--------- Window move (vim keys) ----------
hl.bind(mainMod .. " + SHIFT + h", hl.dsp.window.move({ direction = "left" }))
hl.bind(mainMod .. " + SHIFT + l", hl.dsp.window.move({ direction = "right" }))
hl.bind(mainMod .. " + SHIFT + k", hl.dsp.window.move({ direction = "up" }))
hl.bind(mainMod .. " + SHIFT + j", hl.dsp.window.move({ direction = "down" }))

--------- Resize active window (arrow and vim keys) ----------
hl.bind(mainMod .. " + CTRL + SHIFT + right", hl.dsp.window.resize({ x = 20, y = 0, relative = true }),
   { description = "Resize right" })
hl.bind(mainMod .. " + CTRL + SHIFT + left", hl.dsp.window.resize({ x = -20, y = 0, relative = true }),
   { description = "Resize left" })
hl.bind(mainMod .. " + CTRL + SHIFT + up", hl.dsp.window.resize({ x = 0, y = -20, relative = true }),
   { description = "Resize up" })
hl.bind(mainMod .. " + CTRL + SHIFT + down", hl.dsp.window.resize({ x = 0, y = 20, relative = true }),
   { description = "Resize down" })
hl.bind(mainMod .. " + CTRL + SHIFT + l", hl.dsp.window.resize({ x = 20, y = 0, relative = true }))
hl.bind(mainMod .. " + CTRL + SHIFT + h", hl.dsp.window.resize({ x = -20, y = 0, relative = true }))
hl.bind(mainMod .. " + CTRL + SHIFT + k", hl.dsp.window.resize({ x = 0, y = -20, relative = true }))
hl.bind(mainMod .. " + CTRL + SHIFT + j", hl.dsp.window.resize({ x = 0, y = 20, relative = true }))

--------- Mouse: move / resize window ----------
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Drag window" })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Resize window" })

--------- Zoom cursor ----------
hl.bind(mainMod .. " + mouse_down", function()
   hl.exec_cmd(
   "hyprctl -q keyword cursor:zoom_factor $(hyprctl getoption cursor:zoom_factor | awk '/^float.*/ {print $2 * 1.1}')")
end)
hl.bind(mainMod .. " + mouse_up", function()
   hl.exec_cmd(
   "hyprctl -q keyword cursor:zoom_factor $(hyprctl getoption cursor:zoom_factor | awk '/^float.*/ {print $2 * 0.9}')")
end)

--------- Workspace switching ----------
for i = 1, 10 do
   local key = i % 10  -- 0 → 10
   hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }), { description = "Workspace " .. i })
end

hl.bind(mainMod .. " + PERIOD", hl.dsp.focus({ workspace = "+1" }), { description = "Next workspace" })
hl.bind(mainMod .. " + COMMA", hl.dsp.focus({ workspace = "-1" }), { description = "Prev workspace" })
hl.bind(mainMod .. " + slash", hl.dsp.focus({ workspace = "previous" }), { description = "Previous workspace" })

--------- Move window to workspace + follow ----------
for i = 1, 10 do
   local key = i % 10
   hl.bind(mainMod .. " + CTRL + " .. key, hl.dsp.window.move({ workspace = i }),
      { description = "Move to workspace " .. i })
end

hl.bind(mainMod .. " + CTRL + h", hl.dsp.window.move({ workspace = "-1" }), { description = "Move to prev workspace" })
hl.bind(mainMod .. " + CTRL + l", hl.dsp.window.move({ workspace = "+1" }), { description = "Move to next workspace" })

--------- Move window to workspace (silent, no follow) ----------
for i = 1, 10 do
   local key = i % 10
   hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i, follow = false }),
      { description = "Move to workspace " .. i .. " (silent)" })
end

--------- Special workspace (scratchpad) ----------
hl.bind(mainMod .. " + RETURN", hl.dsp.workspace.toggle_special("scratchpad"), { description = "Toggle scratchpad" })

--------- Media keys ----------
hl.bind("XF86AudioRaiseVolume",
   hl.dsp.exec_cmd(
   "pactl set-sink-volume @DEFAULT_SINK@ +5% && pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\\d+(?=%)' | awk '{if($1>100) system(\"pactl set-sink-volume @DEFAULT_SINK@ 100%\")}' && pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\\d+(?=%)' | awk '{print $1}' | head -1 > /tmp/$HYPRLAND_INSTANCE_SIGNATURE.wob"),
   { repeating = true, locked = true, description = "Volume up" })

hl.bind("XF86AudioLowerVolume",
   hl.dsp.exec_cmd(
   "pactl set-sink-volume @DEFAULT_SINK@ -5% && pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\\d+(?=%)' | awk '{print $1}' | head -1 > /tmp/$HYPRLAND_INSTANCE_SIGNATURE.wob"),
   { repeating = true, locked = true, description = "Volume down" })

hl.bind("XF86AudioMute",
   hl.dsp.exec_cmd(
   "amixer sset Master toggle | sed -En '/\\[on\\]/ s/.*\\[([0-9]+)%\\].*/\\1/ p; /\\[off\\]/ s/.*/0/p' | head -1 > /tmp/$HYPRLAND_INSTANCE_SIGNATURE.wob"),
   { locked = true, description = "Mute" })

hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true, description = "Play/Pause" })
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true, description = "Next track" })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true, description = "Previous track" })

--------- Screen brightness ----------
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -d intel_backlight s +5%"),
   { repeating = true, locked = true, description = "Brightness up" })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -d intel_backlight s 5%-"),
   { repeating = true, locked = true, description = "Brightness down" })
