"            /##            /######            /##
"           | ##           /##__  ##          |__/
"   /###### | ##  /###### | ##  \__//##    /## /## /######/####
"  |____  ##| ## /##__  ##| ####   |  ##  /##/| ##| ##_  ##_  ##
"   /#######| ##| ########| ##_/    \  ##/##/ | ##| ## \ ## \ ##
"  /##__  ##| ##| ##_____/| ##       \  ###/  | ##| ## | ## | ##
" |  #######| ##|  #######| ##   /##  \  #/   | ##| ## | ## | ##
"  \_______/|__/ \_______/|__/  |__/   \_/    |__/|__/ |__/ |__/

" ==========================================
" -| install plugins |----------------------
" ==========================================

" first check that vim-plug is installed
if empty(glob('~/.local/share/nvim/site/autoload/plug.vim'))
  silent !curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs
    \ https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

call plug#begin('~/.vim/plugged')

Plug 'preservim/nerdcommenter'
Plug 'joshdick/onedark.vim'
Plug 'itchyny/lightline.vim'
Plug 'mhinz/vim-startify'
Plug 'junegunn/goyo.vim'
Plug 'kjwon15/vim-transparent'
" Plug 'sheerun/vim-polyglot'
Plug 'mbbill/undotree'
Plug 'tpope/vim-fugitive'
Plug 'airblade/vim-gitgutter'
Plug 'ryanoasis/vim-devicons'
Plug 'vim-syntastic/syntastic'
Plug 'vifm/vifm.vim'
Plug 'vim-scripts/bash-support.vim'
Plug 'gko/vim-coloresque'
Plug 'itchyny/vim-cursorword'

call plug#end()

" ==========================================
" -| mappings |-----------------------------
" ==========================================

" primary mappings
let mapleader=" "
let maplocalleader=","
nnoremap ; :
vnoremap ; :
inoremap jk <esc>
" putting arrow keys to good use (or no use at all)
inoremap <left> <nop>
inoremap <down> <nop>
inoremap <up> <nop>
inoremap <right> <nop>
nnoremap <left> <nop>
nnoremap <right> <nop>
nnoremap <up> ddkP
nnoremap <down> ddp
nnoremap <silent> <C-Left> :vert res -3<CR>
nnoremap <silent> <C-Right> :vert res +3<CR>
nnoremap <silent> <C-Up> :res +3<CR>
nnoremap <silent> <C-Down> :res -3<CR>
" shortcuts for quick vimrc and bashrc editing
nnoremap <silent> <leader>ev :vsplit $MYVIMRC<CR>
nnoremap <silent> <leader>eb :vsplit ~/.bashrc<CR>
" goyo
nnoremap <silent> <leader>zz :Goyo<CR>
" background transparency
nnoremap <silent> <leader>te :TransparentEnable<CR>
nnoremap <silent> <leader>td :TransparentDisable<CR>
" vim-plug commands
nnoremap <silent> <leader>pi :PlugInstall<CR>
nnoremap <silent> <leader>pu :PlugUpdate<CR>
nnoremap <silent> <leader>pg :PlugUpgrade<CR>
nnoremap <silent> <leader>pc :PlugClean<CR>
" file operations
nnoremap <silent> <leader>ff :Vifm<CR>
nnoremap <leader>fs :write<CR>
nnoremap <leader>fq :wq<CR>
" buffer operations
" nnoremap <silent> <leader>bd :bdelete<CR>
" split operations
nnoremap <silent> <leader>sh :split<CR>
nnoremap <silent> <leader>sv :vsplit<CR>
nnoremap <leader>wc <C-w>c
nnoremap <leader>wh <C-w>h
nnoremap <leader>wj <C-w>j
nnoremap <leader>wk <C-w>k
nnoremap <leader>wl <C-w>l
" misc mappings
nnoremap <silent> <leader>ll :set list!<CR>
nnoremap <silent> <leader>hc :helpclose<CR>
nnoremap <silent> <leader>ut :UndotreeToggle<CR>
nnoremap <silent> <leader>lc :nohl<CR>
" emergency quit
nnoremap <leader>qq :qa!<CR>

" ==========================================
" -| general settings |---------------------
" ==========================================

filetype plugin indent on
set cmdheight=1
set cmdheight=2
set cursorline
set encoding=utf-8
set expandtab
set fileencoding=utf-8
set fileencodings=ucs-bom,utf-8,gbk,cp936,latin-1
set fileformat=unix
set fileformats=unix,dos,mac
set fillchars+=vert:⏽
set hidden
set ignorecase
set incsearch
set laststatus=2
set list
set listchars=eol:¬,tab:▸\ ,extends:›,precedes:‹,space:·,trail:~
set mouse=nv
set nocursorcolumn
set noerrorbells
set noshowmode
set nospell
set nowrap
set number relativenumber
set shiftwidth=4
set showmatch
set showtabline=2
set signcolumn=yes
set smartcase
set smartindent
set splitbelow
set splitright
set tabstop=4 softtabstop=4
set timeout
set timeoutlen=750
set ttimeout
set undofile
set undodir=$HOME/.vim/undohistory
set undolevels=1000
set undoreload=10000
set updatetime=250
set visualbell
syntax on
syntax on
syntax on
" keep extra lines above/below cursor when scrolling past top/bottom of buffer
if !&scrolloff
    set scrolloff=3
endif
if !&sidescrolloff
    set sidescrolloff=5
endif
set nostartofline

" ==========================================
" -| plugin/theme settings |----------------
" ==========================================

" let g:loaded_netrw=1
" let g:loaded_netrwPlugin=1

let g:vifm_replace_netrw=1

colorscheme onedark
set background=dark

let g:netrw_banner=0
let g:netrw_browse_split=2
let g:netrw_liststyle=3
let g:netrw_winsize=20

let g:goyo_height='85%'
let g:goyo_width='65%'

set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*
let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_sh_shellcheck_args = "-x"

if !exists('g:undotree_WindowLayout')
    let g:undotree_WindowLayout = 1
endif

" e.g. using 'd' instead of 'days' to save some space.
if !exists('g:undotree_ShortIndicators')
    let g:undotree_ShortIndicators = 0
endif

" undotree window width
if !exists('g:undotree_SplitWidth')
    if g:undotree_ShortIndicators == 1
        let g:undotree_SplitWidth = 35
    else
        let g:undotree_SplitWidth = 40
    endif
endif

if exists('+termguicolors')
    let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
    let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
    set termguicolors
endif

let g:lightline = {
            \ 'active': {
            \   'left': [ [ 'mode', 'paste', 'gitbranch' ],
            \             [ 'readonly', 'filetype', 'absolutepath', 'modified' ] ],
            \   'right': [ [ 'fileformat', 'fileencoding' ],
            \              [ 'percent' ],
            \              [ 'lineinfo' ] ]
            \ },
            \ 'colorscheme': 'one',
            \ 'component': {
            \   'bufnum': 'buf %n',
            \   'lineinfo': ' %3l:%-2v',
            \ },
            \ 'component_function': {
            \   'readonly': 'LightlineReadonly',
            \   'gitbranch': 'LightlineFugitive',
            \   'filetype': 'MyFiletype',
            \   'fileformat': 'MyFileformat',
            \ },
            \ 'enable': {
            \   'tabline': 1,
            \ },
            \ 'mode_map': {
            \   'n' : 'normal',
            \   'i' : 'insert',
            \   'R' : 'replace',
            \   'v' : 'visual',
            \   'V' : 'v-line',
            \   "\<C-v>" : 'v-block',
            \   'c' : 'command',
            \   's' : 'select',
            \   'S' : 's-line',
            \   "\<C-s>" : 's-block',
            \   't' : 'terminal',
            \ },
            \ 'separator': { 'left': '', 'right': '' },
            \ 'subseparator': { 'left': '', 'right': '' },
            \ 'tab': {
            \   'active': [ 'tabnum', 'filename', 'modified' ]
            \ },
            \ }

let g:NERDSpaceDelims=1
let g:NERDCommentEmptyLines=1
let g:NERDDefaultAlign='left'
let g:NERDTrimTrailingWhitespace=1
let g:NERDToggleCheckAllLines=1

let g:ascii = [
\'//=====================================\\',
\'||         :            -`             ||',
\'||       .dM:          /Md/.``         ||',
\'||       hMMm:         hMMMMMNds-      ||',
\'||      hMMMMh-       oNMMMMMMMM.      ||',
\'||      -mMMMMMy.      :sdNMNNNm.      ||',
\'||       .yNMMMMNs.      .dm:```       ||',
\'||         :hMMMMMm+`   .mm-           ||',
\'||          .sMMMMMMd/` hM:            ||',
\'||        -sdy/+mMMMMMdoMd             ||',
\'||       oNM:   `oNMMMMMMm`            ||',
\'||      oMMN`     .sNMMMMMh.           ||',
\'||      hMMMs       -yMMMMMNo`         ||',
\'||      +MMMMy`       :hMMMMMm+        ||',
\'||       hMMMMm.       `/dMMMMMy       ||',
\'||       `NMMMMm`        `+mMMMM-      ||',
\'||        hMMMMM/          `sMMM.      ||',
\'||        `NMMMMm`        `+mMMMM-     ||',
\'||         hMMMMM/          `sMMM.     ||',
\'||       .ohhhhhs`            hm:      ||',
\'\\=====================================//'
\]
let g:startify_custom_header = 'startify#center(g:ascii)'
let g:startify_files_number = 5

" ==========================================
" -| functions |----------------------------
" ==========================================

function! MyFiletype()
    return winwidth(0) > 70 ? (strlen(&filetype) ? &filetype . ' ' . WebDevIconsGetFileTypeSymbol() : 'no ft') : ''
endfunction

function! MyFileformat()
    return winwidth(0) > 70 ? (&fileformat . ' ' . WebDevIconsGetFileFormatSymbol()) : ''
endfunction

function! LightlineReadonly()
    return &readonly ? '' : ''
endfunction

function! LightlineFugitive()
    if exists('*FugitiveHead')
        let branch = FugitiveHead()
        return branch !=# '' ? ''.branch : ''
    endif
    return ''
endfunction

" ==========================================
" -| autocommands |-------------------------
" ==========================================

" entering insert mode automatically in gitcommit files
augroup git_stuff
    autocmd!
    autocmd BufEnter * if &filetype == 'gitcommit' | startinsert | endif
augroup END

" always open help in vertical split 
augroup vimrc_help
    autocmd!
    autocmd BufEnter *.txt if &buftype == 'help' | wincmd L | endif
augroup END

" enable yanking into windows clipboard via (y)ank and (d)elete ops
let s:clip = '/mnt/c/Windows/System32/clip.exe'
if executable(s:clip)
    augroup WSLYank
        autocmd!
        autocmd TextYankPost * if v:event.operator ==# 'y' | call system(s:clip, @0) | endif
        autocmd TextYankPost * if v:event.operator ==# 'd' | call system(s:clip, @1) | endif
    augroup END
endif