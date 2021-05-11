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

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1="\n\[$(tput setaf 4)\][\[$(tput setaf 5)\]\w\[$(tput setaf 4)\]]\n\[$(tput setaf 6)\]\u\[$(tput setaf 5)\]@\[$(tput setaf 6)\]\h\[$(tput setaf 5)\]\\$ \[$(tput sgr0)\]"
else
    PS1='\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# enable color support of ls and also add handy aliases
# [[ -x /usr/bin/dircolors ]] && [[ -r ~/.dircolors ]] && eval '$(dircolors -b ~/.dircolors >/dev/null 2>&1' || eval '$(dircolors -b) >/dev/null 2>&1'
if [ -x /usr/bin/dircolors ]; then
    if [ -r ~/.dircolors ]; then
        eval "$(dircolors -b ~/.dircolors)"
    else
        eval "$(dircolors -b)"
    fi
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
fi

export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# enable programmable completion features
if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        # shellcheck source=/usr/share/bash-completion/bash_completion
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

########################
# user specified stuff #
########################

# shellcheck source=/home/alef/.bash_aliases
[ -f ~/.bash_aliases ] && . ~/.bash_aliases

export MANPAGER="sh -c 'col -bx | bat -l man -p'"
export BROWSER="firefox"
export PATH="$PATH:/mnt/d/Programs/processing/processing-java"
export PATH="$PATH:/home/linuxbrew/.linuxbrew/bin"
export MANPATH="$MANPATH:/home/linuxbrew/.linuxbrew/share/man"
export INFOPATH="$INFOPATH:/home/linuxbrew/.linuxbrew/share/info"
export LESSHISTFILE=/dev/null
export VISUAL=nvim
export EDITOR="$VISUAL"
DISPLAY=$(grep "nameserver" /etc/resolv.conf | awk '{print $2; exit;}'):0.0
export DISPLAY
export LIBGL_ALWAYS_INDIRECT=1
eval "$(hub alias -s) > /dev/null 2>&1"
eval "keychain --eval --agents ssh id_ed25519 > /dev/null 2>&1"
[[ -z "$(pgrep cron)" ]] && sudo /etc/init.d/cron start > /dev/null 2>&1
cln
