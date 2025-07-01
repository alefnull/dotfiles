if status is-interactive
    # Commands to run in interactive sessions can go here
end

set -Ux EDITOR nvim

alias cls='clear && fastfetch'
alias ls='eza --color=auto --git -lh'
alias ll='eza --color=auto --git -lah'
alias cat='bat'
alias lg='lazygit'
alias lf='y'
