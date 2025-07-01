set -gx EDITOR nvim
set -gx GIT_EDITOR nvim

set -gx DOTFILES "$HOME/dotfiles"

alias cls='clear && fastfetch'
alias ls='eza --color=auto --git -lh'
alias ll='eza --color=auto --git -lah'
alias cat='bat'
alias lg='lazygit'
alias lf='y'
