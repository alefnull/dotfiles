source /usr/share/cachyos-fish-config/cachyos-config.fish

set -gx IDEA_JDK "/home/alef/.jbr/jbr_jcef-21.0.7-linux-x64-b895.130-1"
set -gx QT_AUTO_SCREEN_SCALE_FACTOR 1
set -gx QT_SCREEN_SCALE_FACTORS 1.25

# overwrite greeting
# potentially disabling fastfetch
function fish_greeting
#    # smth smth
    cls
end

eval "$(atuin init fish)"

