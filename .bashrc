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

# export FZF_DEFAULT_COMMAND="find . -type f"
export FZF_DEFAULT_COMMAND="ag -l --hidden --depth 3"
export FZF_DEFAULT_OPTS="--cycle --no-height --reverse --border=rounded --pointer='=>' --ansi --tabstop=4"
export FZF_DEFAULT_OPTS=$FZF_DEFAULT_OPTS'
--color=dark
--color=fg:-1,bg:-1,hl:#c678dd,fg+:#eeeeee,bg+:#4b5263,hl+:#d858fe
--color=info:#98c379,prompt:#c678dd,pointer:#c678dd,marker:#c678dd,spinner:#61afef,header:#61afef
--color=gutter:-1'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="--border=rounded --preview 'batcat --color=always --line-range :50 {}'"
# export FZF_ALT_C_COMMAND="find . --type d"
export FZF_ALT_C_OPTS="--border=rounded --preview 'tree -C {} | head -50'"
export FZF_TMUX=1
export TMUX_FZF_ORDER="session|window|pane|command|keybinding"

eval "$(hub alias -s) > /dev/null 2>&1"
eval "keychain --eval --agents ssh id_ed25519 > /dev/null 2>&1"
cln

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

[ -f ~/.fzf.bash ] && source ~/.fzf.bash
[ -f ~/.config/scripts/fzfuncs.sh ] && source ~/.config/scripts/fzfuncs.sh

