#!/usr/bin/env bash

# useful stuff
alias .repo="cd ~/dev/dotfiles && git status"
alias clr="clear"
alias cln="clr && now | lolcat && tdo | lolcat"
alias vi="nvim"
alias vim="nvim"
alias cat="bat --theme OneHalfDark --style full"
alias brc="vi ~/.bashrc"
alias vrc="vi ~/.config/nvim/init.vim"
alias ll="ls -Al"
alias la="ls -A"
alias cls="clear && la"
alias reload="source ~/.bashrc && cln"
alias gs="git status"
alias gp="git push"
alias gd="git diff"

# fun stuff
alias now="date +%r"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -f pagga.tlf"
alias bfig="toilet -F border -f pagga.tlf"
