#!/usr/bin/env bash 
#===============================================================================
#
#          FILE: bootstrap.sh
#
#         USAGE: ./bootstrap.sh (insert 'curl <github-raw-url-here> | /bin/bash' command here)
#
#   DESCRIPTION: a basic script to pull down bare repo of dotfiles and do some setup
#
#       OPTIONS: ---
#  REQUIREMENTS: bash, curl, git, ??
#        AUTHOR: alefnull (nullalef@gmail.com), 
#       CREATED: 04/26/20 01:52
#===============================================================================

set -e
set -o nounset

dotdir="$HOME"/.dots
if [ -d "$dotdir" ]; then
    echo "$dotdir already exists. aborting."
    exit 1
else
    mkdir -p "$dotdir"
fi

git clone --bare git@github.com:alefnull/dotfiles.git "$dotdir"

function dot {
    /usr/bin/git --git-dir="$dotdir"/ --work-tree="$HOME" "$@"
}


if dot checkout
then
    echo "dotfiles successfully checked out.";
else
    echo "existing files found. backing up to '$dotdir'.";
    dot checkout 2>&1 | grep -E "\s+\." | awk "{'print $1'}" | xargs -I{} mv {} .backup-cfg/{}
fi;

dot checkout
dot config status.showUntrackedFiles no
exit 0
