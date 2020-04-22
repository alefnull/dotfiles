#!/usr/bin/env bash

# If not running interactively, don't do anything
[[ $- == *i* ]] || return

set -o vi
shopt -s checkwinsize
shopt -s histappend
HISTCONTROL=ignoreboth
HISTSIZE=10000
HISTFILESIZE=10000
HISTTIMEFORMAT="%T %t"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

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
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
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
export LF_ICONS="\
di=::fi=:ln=:or=:ex=:\
*.viminfo=:*.vimrc=:*.vim=:\
*.bashrc=:\
*.git=:\
*.gitignore=:\
*.c=:*.cc=:*.clj=:*.coffee=:*.cpp=:*.css=:\
*.d=:*.dart=:\
*.erl=:*.exs=:\
*.fs=:\
*.go=:\
*.h=:*.hh=:*.hpp=:*.hs=:*.html=:\
*.java=:*.jl=:*.js=:*.json=:\
*.lua=:\
*.md=:\
*.php=:*.pl=:*.pro=:*.py=:\
*.rb=:*.rs=:\
*.scala=:\
*.ts=:\
*.cmd=:*.ps1=:*.sh=:*.bash=:*.zsh=:*.fish=:\
*.tar=:*.tgz=:*.arc=:*.arj=:*.taz=:*.lha=:*.lz4=:*.lzh=:\
*.lzma=:*.tlz=:*.txz=:*.tzo=:*.t7z=:*.zip=:\
*.z=:*.dz=:*.gz=:*.lrz=:*.lz=:*.lzo=:*.xz=:*.zst=:\
*.tzst=:*.bz2=:*.bz=:*.tbz=:*.tbz2=:*.tz=:\
*.deb=:*.rpm=:*.jar=:*.war=:*.ear=:*.sar=:*.rar=:\
*.alz=:*.ace=:*.zoo=:*.cpio=:*.7z=:*.rz=:\
*.cab=:*.wim=:*.swm=:*.dwm=:*.esd=:*.jpg=:*.jpeg=:\
*.mjpg=:*.mjpeg=:*.gif=:*.bmp=:*.pbm=:*.pgm=:\
*.ppm=:*.tga=:*.xbm=:*.xpm=:*.tif=:*.tiff=:*.png=:\
*.svg=:*.svgz=:*.mng=:*.pcx=:*.mov=:*.mpg=:\
*.mpeg=:*.m2v=:*.mkv=:*.webm=:*.ogm=:*.mp4=:*.m4v=:\
*.mp4v=:*.vob=:*.qt=:*.nuv=:*.wmv=:*.asf=:\
*.rm=:*.rmvb=:*.flc=:*.avi=:*.fli=:*.flv=:*.gl=:\
*.dl=:*.xcf=:*.xwd=:*.yuv=:*.cgm=:*.emf=:\
*.ogv=:*.ogx=:*.aac=:*.au=:*.flac=:*.m4a=:*.mid=:\
*.midi=:*.mka=:*.mp3=:*.mpc=:*.ogg=:*.ra=:\
*.wav=:*.oga=:*.opus=:*.spx=:*.xspf=:*.pdf=:*.nix=:"

export BROWSER="firefox"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export MANPATH="/home/linuxbrew/.linuxbrew/share/man:$MANPATH"
export INFOPATH="/home/linuxbrew/.linuxbrew/share/info:$INFOPATH"
export LESSHISTFILE=/dev/null
export TODO="$HOME/.tdon"
export VISUAL=nvim
export EDITOR="$VISUAL"
DISPLAY=$(grep "nameserver" /etc/resolv.conf | awk '{print $2; exit;}'):0.0
export DISPLAY
export LIBGL_ALWAYS_INDIRECT=1
export NVM_DIR="$HOME/.nvm"
export RANGER_LOAD_DEFAULT_RC=false
# shellcheck disable=SC1090
# [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
# shellcheck disable=SC1090
# [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
# shellcheck source=/home/alef/dev/tdon.sh/tdon.sh
source "$HOME/dev/tdon.sh/tdon.sh"
eval "$(hub alias -s) > /dev/null 2>&1"
eval "$(starship init bash) > /dev/null 2>&1"
eval "keychain --eval --agents ssh id_rsa > /dev/null 2>&1"
cln
