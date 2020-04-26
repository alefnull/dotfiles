#!/usr/bin/env bash 

set -e
set -o nounset

dot_dir="$HOME"/.dots
if [ -d "$dot_dir" ]; then
    echo "$dot_dir already exists. aborting."
    exit 1
fi

mkdir -p "$dot_dir"
git clone --bare git@github.com:alefnull/dotfiles.git "$dot_dir"

which_git="$(which git)"
function dot { "$which_git" --git-dir="$dot_dir"/ --work-tree="$HOME" "$@"; }

dot config status.showUntrackedFiles no
dot checkout -f
exit 0
