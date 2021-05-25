GREEN="\[\033[0;32m\]"
CYAN="\[\033[0;36m\]"
RED="\[\033[0;31m\]"
PURPLE="\[\033[0;35m\]"
BROWN="\[\033[0;33m\]"
LIGHT_GRAY="\[\033[0;37m\]"
LIGHT_BLUE="\[\033[1;34m\]"
LIGHT_GREEN="\[\033[1;32m\]"
LIGHT_CYAN="\[\033[1;36m\]"
LIGHT_RED="\[\033[1;31m\]"
LIGHT_PURPLE="\[\033[1;35m\]"
YELLOW="\[\033[1;33m\]"
WHITE="\[\033[1;37m\]"
RESTORE="\[\033[0m\]" #0m restores to the terminal's default colour

BRANCH=""
if which git &>/dev/null; then
    BRANCH=$(git branch 2>/dev/null | grep \* |  cut -d " " -f 2)
fi
echo "\n${PURPLE}[${LIGHT_CYAN}\w${PURPLE}] ${LIGHT_BLUE}${BRANCH}\n${LIGHT_BLUE}\u${PURPLE}@${LIGHT_BLUE}\h ${PURPLE}\$ $RESTORE"
