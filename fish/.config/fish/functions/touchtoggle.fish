function touchtoggle
  if not set -q touch_enabled
    hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled false
    set -U touch_enabled 0
    notify-send -t 2000 "touchpad toggled: ON"
  else if [ $touch_enabled = 0 ]
    hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled true
    set -U touch_enabled 1
    notify-send -t 2000 "touchpad toggled: ON"
  else if [ $touch_enabled = 1 ]
    hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled false
    set -U touch_enabled 0
    notify-send -t 2000 "touchpad toggled: OFF"
  end
end
