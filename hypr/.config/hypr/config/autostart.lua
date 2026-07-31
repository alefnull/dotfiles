-- autostart.lua
-- Commands run on Hyprland startup (was exec-once)

hl.on("hyprland.start", function()
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("waypaper --restore")
    hl.exec_cmd("swaync")
    hl.exec_cmd("sunsetr")
    hl.exec_cmd("hyprctl setcursor \"Catppuccin Mocha Light\" 32")
    hl.exec_cmd("bash -c \"sleep 1 && RIVET_SILENT=1 /home/alef/.cargo/bin/rivet\"")
end)
