#!/usr/bin/env bash

# useful stuff
alias .repo="cd /mnt/d/dev/dotfiles && git status"
alias clr="clear"
alias cln="clr && now && weather && tdo | lolcat && echo ''"
alias vi="nvim"
alias vim="nvim"
alias cat="batcat --theme OneHalfDark --style full"
alias brc="code ~/.bashrc"
alias ll="ls -Al"
alias la="ls -A"
alias cls="clear && la"
alias lint="standard --verbose | snazzy"
alias reload="source ~/.bashrc && cln"

# fun stuff
alias now="date +%r"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1

# temporary COVID-19 tracker alias
alias covid="curl https://covid19tracker.xyz/"
alias covidus="curl https://covid19tracker.xyz/us"
