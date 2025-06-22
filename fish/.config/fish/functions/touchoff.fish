function touchoff
  hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled false
  set -U touch_enabled 0
end
