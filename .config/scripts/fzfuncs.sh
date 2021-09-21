#!/usr/bin/env bash
# -*- coding: utf-8 -*-

usage() {
    echo "fz - a set of tools using FZF and AG to manage files and navigate directories quickly"
    echo ""
    echo "usage: fz [command] [search pattern]"
    echo ""
    echo "commands:"
    echo "   fz  - print usage info"
    echo "   fze - open file in editor"
    echo "   fzd - cd to directory/file"
    echo "   fzb - checkout git branch, including remote branches"
    echo "   fzc - git commit browser"
    echo "   fzg - create gitignore file from gitiignore.io"
    echo "   fzm - manpage explorer"
}

# functions
# =========
# fz - print usage info
fz() {
  # if no arguments, print usage info
  if [ $# -eq 0 ]; then
      usage
  fi
  # if one argument, run corresponding command, passing the rest of the arguments
  if [ $# -eq 1 ]; then
    case $1 in
      e) fze "${@:2}" ;;
      d) fzd "${@:2}" ;;
      b) fzb "${@:2}" ;;
      c) fzc "${@:2}" ;;
      g) fzg "${@:2}" ;;
      m) fzm "${@:2}" ;;
      *) echo "unknown command: $1" ;;
    esac
  fi
}

# fze - open file in editor
fze() {
  local file
  # use ag to find files
  list=$(ag -l --hidden --depth 4)
  # filter out directories
  list=$(echo "$list" | grep -v '/$')
  # use fzf to select file
  file=$(echo "$list" | fzf)
  # make sure file exists
  if [ -f "$file" ]; then
    # open file in editor
    $EDITOR "$file"
  fi
}

# fzd - cd to directory/file
#
# usage: fzd [search pattern]
fzd() {
  local dir
  # use fd to find directories
  list=$(fd -t d -H 2>/dev/null)
  # use fzf to select directory
  dir=$(echo "$list" | fzf)
  # make sure directory exists
  if [ -d "$dir" ]; then
    # cd to directory
    cd "$dir"
  fi
}

# fzb - checkout git branch, including remote branches
#
# usage: fzb [search pattern]
fzb() {
    git checkout $(git branch -a | fzf | sed 's/^..//')
}

# fzc - git commit browser
#
# usage: fzc
alias glNoGraph='git log --color=always --format="%C(auto)%h%d %s %C(black)%C(bold)%cr% C(auto)%an" "$@"'
_gitLogLineToHash="echo {} | grep -o '[a-f0-9]\{7\}' | head -1"
_viewGitLogLine="$_gitLogLineToHash | xargs -I % sh -c 'git show --color=always %'"
fzc() {
    glNoGraph |
        fzf --no-sort --reverse --tiebreak=index --no-multi \
            --ansi --preview="$_viewGitLogLine" \
                --header "enter to view, alt-y to copy hash" \
                --bind "enter:execute:$_viewGitLogLine   | batcat --color=always" \
                --bind "alt-y:execute:$_gitLogLineToHash | xclip"
}

# fzg - create gitignore file from gitiignore.io
#
# usage: fzg [search pattern]
fzg() {
  if [ "$#" -eq 0 ]; then
    IFS+=','
    for i in $( curl -L -s "https://www.toptal.com/developers/gitignore/api/list" ); do
      echo "$i"
    done | fzf --prompt="select gitignore templates: " --multi --ansi | paste -s -d "," - | {
      # if no pattern is selected, exit
      read -r pattern
      if [ -z "$pattern" ]; then
        exit
      fi
      # if pattern is selected, create gitignore file
      curl -L -s "https://www.toptal.com/developers/gitignore/api/$pattern" > .gitignore
      # print message
      echo -e "\ngenerated .gitignore file for $pattern"
    }
  else
    # if pattern is specified, create gitignore file
    curl -L -s "https://www.toptal.com/developers/gitignore/api/$@" > .gitignore
    # print message
    echo -e "\ngenerated .gitignore file for $pattern"
  fi
}

# fzm - manpage explorer using fzf
#
# usage: fzm [manpage]
fzm() {
  # if no argument is given, display a list of manpages and select one with fzf
  if [[ -z $1 ]]; then
    # use fzf to select a manpage,
    # strip the first word (the command name) and display the manpage
    manpage=$(man -k . | fzf | awk '{print $1;}')
    man $manpage
  else
    man $1
  fi
}

