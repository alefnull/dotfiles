#!/usr/bin/env bash

# useful stuff
alias dots="cd ~/dev/dotfiles && git status && ll"
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias fm="ranger"
alias cat="bat --theme OneHalfDark --style full"
alias brc="vi ~/.bashrc"
alias bls="vi ~/.bash_aliases"
alias vrc="vi ~/.config/nvim/init.vim"
alias ll="exa -alh --git"
# alias la="ls -A"
alias ls="exa"
alias clr="clear"
alias cls="clr && ll"
alias cln="clr && now | lolcat"
alias reload="source ~/.bashrc && cln"
alias gc="git commit -a"
alias gs="lazygit"
alias gp="git push"
alias gd="git difftool -y"
alias du="ncdu"

# fun stuff
alias now="date +%r"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -k -f hash3d-ne.flf"
alias news="newsboat -r"
