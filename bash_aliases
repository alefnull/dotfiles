#!/usr/bin/env bash

# useful stuff
alias dots="cd ~/dev/dotfiles && git status && ll"
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias fm="ranger"
alias cat="bat --theme OneHalfDark --style full"
alias brc="vi ~/dev/dotfiles/bashrc"
alias bls="vi ~/dev/dotfiles/bash_aliases"
alias vrc="vi ~/dev/dotfiles/vimrc"
alias ll="exa -alh --git"
# alias la="ls -A"
alias ls="exa"
alias clr="clear"
alias cls="clr && ll"
alias reload="source ~/.bashrc"
alias gc="git commit -a"
alias gs="lazygit"
alias gp="git push"
alias gd="git difftool -y"
alias du="ncdu"

# fun stuff
alias center="sed -e :a -e 's/^.\{1,77\}$/ & /;ta'"
alias ck="fortune -e education science tao linux anarchism computers news literature pratchett drugs paradoxum politics magic disclaimer wisdom law"
alias now="date +%A,\ %B\ %d,\ %Y | center | lolcat && date +%r | center | lolcat"
alias cln="clr && fig omen | center | lolcat && now | center | lolcat && echo '' && ck | center"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -k -f hash3d"
alias news="newsboat -r"
