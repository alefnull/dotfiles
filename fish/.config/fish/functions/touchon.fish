function touchon
  hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled true
  set -U touch_enabled 1
end
