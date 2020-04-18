#!/usr/bin/env bash

# useful stuff
alias dots="cd ~/dev/dotfiles && git status"
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias vfm="vifm"
alias fm="vifm"
alias cat="bat --theme OneHalfDark --style full"
alias brc="vi ~/.bashrc"
alias bls="vi ~/.bash_aliases"
alias vrc="vi ~/.config/nvim/init.vim"
alias ll="ls -Al"
alias la="ls -A"
alias clr="clear"
alias cls="clr && ll"
alias cln="clr && now | lolcat && tdo | lolcat"
alias reload="source ~/.bashrc && cln"
alias gc="git commit -a"
alias gs="git status"
alias gp="git push"
alias gd="git diff"
alias du="ncdu"

# fun stuff
alias now="date +%r"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -f pagga.tlf"
alias bfig="toilet -F border -f pagga.tlf"
