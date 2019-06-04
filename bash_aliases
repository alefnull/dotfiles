# useful stuff
alias .repo="cd /mnt/c/Users/alef/Documents/Projects/dotfiles && git status"
alias nf="clear && neofetch"
alias vi="nvim"
alias cat="bat --theme TwoDark --style full"
alias brc="nano ~/.bashrc"
alias cls="clear && ls"
alias ll="ls -Al"

# fun stuff
alias m="cmatrix -ab"
alias now="date +%r"
alias 2048="2048-in-terminal"

# curl wttr.in -- up until the follow reminder (for minimalism's sake)
alias weather="curl --fail --silent --show-error wttr.in/?1q | sed '/Follow/Q'" 2>&1
