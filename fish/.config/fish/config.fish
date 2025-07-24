set -gx XDG_CONFIG_HOME "$HOME/.config"
set -gx XDG_DATA_HOME "$HOME/.local/share"
set -gx XDG_STATE_HOME "$HOME/.local/state"
set -gx XDG_CACHE_HOME "$HOME/.cache"

set -gx EDITOR nvim
set -gx GIT_EDITOR nvim

set -gx DOTFILES "$HOME/dotfiles"
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
alias zj='zellij --layout compact'

zellij_update_tabname

# Added by LM Studio CLI (lms)
set -gx PATH $PATH /home/alef/.lmstudio/bin
# End of LM Studio CLI section

