-- defaults.lua
-- Shared variables used across the config
-- Globals so all required modules can reference them directly

filemanager = "pcmanfm"
applauncher = "pkill -x wofi >/dev/null 2>&1 || wofi -i --show drun"
wmenu = "pkill -x wmenu-drun >/dev/null 2>&1 || wmenu-drun"
emojipicker = "pkill -x wmenu-emoji >/dev/null 2>&1 || wmenu-emoji"
wallswitcher = "pkill -x waypaper >/dev/null 2>&1 || waypaper"
terminal = "kitty"
idlehandler = "swayidle -w timeout 300 'swaylock -f -c 000000' before-sleep 'swaylock -f -c 000000'"
capturing = "hyprshot -m region -r - | swappy -f -"
screencap = "hyprshot -m output -m eDP-1 -r - | swappy -f -"
browser = "zen-browser"
discord = "legcord"
