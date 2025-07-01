function touchenable
    hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled true
end

function touchdisable
    hyprctl keyword device[gxtp5100:00-27c6:01e0-touchpad]:enabled false
end

function touchtoggle
    # set touch_enabled based on bool in a local .touch file (create if it doesn't exist)
    set -l touch_enabled (cat ~/.touch 2>/dev/null)
    if test "$touch_enabled" = true
        touchdisable
        echo false >~/.touch
        notify-send -t 2000 "touchpad disabled"
    else
        touchenable
        echo true >~/.touch
        notify-send -t 2000 "touchpad enabled"
    end
end
