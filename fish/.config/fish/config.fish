set -gx XDG_CONFIG_HOME "$HOME/.config"
set -gx XDG_DATA_HOME "$HOME/.local/share"
set -gx XDG_STATE_HOME "$HOME/.local/state"
set -gx XDG_CACHE_HOME "$HOME/.cache"

set -gx QT_QPA_PLATFORM "wayland;xcb"

set -gx CUDA_VISIBLE_DEVICES 0
set -gx OLLAMA_GPU_MEMORY_FRACTION 0.8

set -gx EDITOR '/home/alef/.local/share/bob/nvim-bin/nvim'
set -gx VISUAL '/home/alef/.local/share/bob/nvim-bin/nvim'
set -gx GIT_EDITOR '/home/alef/.local/share/bob/nvim-bin/nvim'

set -gx DOTFILES "$HOME/dotfiles"
set -gx RACK_DIR "$HOME/dev/Rack-SDK"
set -gx RACK_USER_DIR "$HOME/.local/share/Rack2"

alias clr='clear'
alias cls='clear && fastfetch'
alias ls='eza --color=auto --git -lh'
alias ll='eza --color=auto --git -lah'
alias cat='bat'
alias lg='lazygit'
alias lf='y'
alias vi='nvim'
alias vim='nvim'

# Added by LM Studio CLI (lms)
set -gx PATH $PATH $HOME/.lmstudio/bin
# End of LM Studio CLI section
set -gx PATH $PATH $HOME/.local/bin

set -gx PATH $PATH $HOME/.local/share/bob/nvim-bin
set -gx SUDO_EDITOR '/home/alef/.local/share/bob/nvim-bin/nvim'

cls
