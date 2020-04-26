#!/usr/bin/env bash

# useful stuff
# alias dots="cd ~/dev/dotfiles && git status && ll"
alias dot='/usr/bin/git --git-dir=$HOME/.dots/ --work-tree=$HOME'
alias dots='dot ls-tree -r master --name-only'
alias dotdiff='dot difftool -y'
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias cat="bat --theme OneHalfDark --style full"
alias brc='nvim $HOME/.bashrc'
alias bls='nvim $HOME/.bash_aliases'
alias vrc='nvim $HOME/.config/nvim/init.vim'
# alias la="ls -A"
alias ls="exa"
alias ll="exa -alh --git"
alias clr="clear"
alias cls="clr && ll"
alias reload='source $HOME/.bashrc'
alias gc="git commit"
alias gs="git status"
alias gp="git push"
alias gd="git difftool -y"
alias du="ncdu"

# fun stuff
alias center="sed -e :a -e 's/^.\{1,77\}$/ & /;ta'"
alias ck="fortune -e education science linux computers news drugs politics magic wisdom law"
alias now="date +%A,\ %B\ %d,\ %Y | center && date +%r | center"
alias cln="clr && fig omen | center | lolcat && now | center && echo '' && ck | center"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -k -f hash3d"
alias news="newsboat -r"
