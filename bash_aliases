#!/usr/bin/env bash

# useful stuff
alias .repo="cd /mnt/d/Dev/GitHub/dotfiles && git status"
alias cln="clear && neofetch && tdo | lolcat"
alias vi="nvim"
alias vim="nvim"
alias cat="bat --theme OneHalfDark --style full"
alias brc="code ~/.bashrc"
alias ll="ls -Al"
alias cls="clear && ll"
alias adb=adb.exe
alias lint="standard --verbose | snazzy"
alias reload="source ~/.bashrc"

# fun stuff
alias m="unimatrix -a -f -o -l kgc -s 90"
alias now="date +%r"

# curl wttr.in -- up until the follow reminder (for minimalism's sake)
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
