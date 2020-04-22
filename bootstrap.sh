#!/usr/bin/env bash

DOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILE=

case $DOTFILE in
    bashrc)
        if [[ -L "$HOME"/.config/"$DOTFILE" ]]; then
            echo "${DOTS[DOTFILE]} already linked!"
        else
            ln -s "${DOTDIR}"/"$DOTFILE" ~/."$DOTFILE"
        fi
        ;;
    bash_aliases)
        if [[ -L "$HOME"/.config/"$DOTFILE" ]]; then
            echo "${DOTS[DOTFILE]} already linked!"
        else
            ln -s "${DOTDIR}"/"$DOTFILE" ~/.config/nvim/init.vim
        fi
        ;;
    vimrc)
        if [[ -L "$HOME"/.config/nvim/init.vim ]]; then
            echo "${DOTS[DOTFILE]} already linked!"
        else
            ln -s "${DOTDIR}"/"$DOTFILE" ~/.config/nvim/init.vim
        fi
        ;;
esac
        # setup symlinks
        ln -s "${DOTDIR}"/bashrc ~/.bashrc
        ln -s "${DOTDIR}"/bash_aliases ~/.bash_aliases
        ln -s "${DOTDIR}"/gitconfig ~/.gitconfig
        ln -s "${DOTDIR}"/htop/htoprc ~/.config/htop/htoprc
        ln -s "${DOTDIR}"/vimrc ~/.config/nvim/init.vim
        ln -s "${DOTDIR}"/starship.toml ~/.config/starship.toml

        if [[ -d "$HOME"/.local/bin ]]; then
            if [[ ! -f "$HOME"/.local/bin/firefox ]]; then
                ln -s "${DOTDIR}"/firefox ~/.local/bin/firefox 
            else
                echo "firefox already linked"
            fi
        else
            mkdir -p ~/.local/bin && ln -s "${DOTDIR}"/firefox ~/.local/bin/firefox
        fi
