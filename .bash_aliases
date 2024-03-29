#!/usr/bin/env bash

# useful stuff
alias repos='cd /mnt/c/Users/alefnull/OneDrive/Documents/GitHub/'
alias src='cd /mnt/c/Users/alefnull/source/'
# alias dots="cd ~/dev/dotfiles && git status && ll"
alias dot='/usr/bin/git --git-dir=$HOME/.dots/ --work-tree=$HOME'
alias dots='echo currently tracked dotfiles: && echo --------------------------- && dot ls-tree -r main --name-only --full-tree ~'
alias dotdiff='dot difftool -y'
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias cat="batcat --theme OneHalfDark --style full"
alias brc='nvim $HOME/.bashrc'
alias bls='nvim $HOME/.bash_aliases'
alias vrc='nvim $HOME/.config/nvim/init.vim'
alias trc='nvim $HOME/.byobu/.tmux.conf'
alias la="ls -a"
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
alias ck="fortune -e science linux computers news drugs politics wisdom"
alias now="date +%A,\ %B\ %d,\ %Y | center && date +%r | center"
alias cln="clr && fig zephyr | center | lolcat && echo && ck | center"
alias cle="clr && fig envs | center | lolcat && echo \"type 'envs' to login.\" | center"
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
alias fig="toilet -k -f hash3d"
alias news="newsboat -r"

# geeky stuff
alias envs="ssh alefnull@envs.net"
alias b="byobu"
alias ebup="sshfs alefnull@envs.net:/home/alefnull/public_html/ /mnt/envs/ && cd /mnt/envs/"
alias ebdown="fusermount -u /mnt/envs/"

