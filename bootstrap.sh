#!/usr/bin/env bash

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# setup symlinks
ln -s "${BASEDIR}"/bashrc ~/.bashrc
ln -s "${BASEDIR}"/bash_aliases ~/.bash_aliases
ln -s "${BASEDIR}"/gitconfig ~/.gitconfig
ln -s "${BASEDIR}"/htop/htoprc ~/.config/htop/htoprc
ln -s "${BASEDIR}"/vimrc ~/.config/nvim/init.vim
