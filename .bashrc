#!/usr/bin/env bash

# If not running interactively, don't do anything
[[ $- == *i* ]] || return

set -o emacs
shopt -s checkwinsize
shopt -s histappend
HISTCONTROL=ignoreboth
HISTSIZE=10000
HISTFILESIZE=10000
HISTTIMEFORMAT="%T %t"

# PS1="\n\[$(tput setaf 4)\][\[$(tput setaf 5)\]\w\[$(tput setaf 4)\]]\n\[$(tput setaf 6)\]\u\[$(tput setaf 5)\]@\[$(tput setaf 6)\]\h\[$(tput setaf 5)\]\\$ \[$(tput sgr0)\]"
function prompt_command {
  export PS1=$(~/.config/scripts/prompt.sh)
}
PROMPT_DIRTRIM=2
PROMPT_COMMAND=prompt_command

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    if [ -r ~/.dircolors ]; then
        eval "$(dircolors -b ~/.dircolors)"
    else
        eval "$(dircolors -b)"
    fi
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
fi

# enable programmable completion features
if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

[ -f ~/.bash_aliases ] && . ~/.bash_aliases

export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
export MANPAGER="sh -c 'col -bx | batcat -l man -p'"
export BROWSER="firefox"
export PATH="$PATH:/mnt/d/Programs/processing/processing-java"
export PATH="$PATH:/home/linuxbrew/.linuxbrew/bin"
export MANPATH="$MANPATH:/home/linuxbrew/.linuxbrew/share/man"
export INFOPATH="$INFOPATH:/home/linuxbrew/.linuxbrew/share/info"
export LESSHISTFILE=/dev/null
export VISUAL=nvim
export EDITOR="$VISUAL"
export LIBGL_ALWAYS_INDIRECT=1
eval "$(hub alias -s) > /dev/null 2>&1"
eval "keychain --eval --agents ssh id_ed25519 > /dev/null 2>&1"
cln
