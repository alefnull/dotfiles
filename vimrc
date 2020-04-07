" ==========================================
" ░░░░░░█▀█░█░░░█▀▀░█▀▀░░░░█░█░▀█▀░█▄█░░░░░░
" ░░░░░░█▀█░█░░░█▀▀░█▀▀░░░░▀▄▀░░█░░█░█░░░░░░
" ░░░░░░▀░▀░▀▀▀░▀▀▀░▀░░░▀░░░▀░░▀▀▀░▀░▀░░░░░░
" ==========================================
"
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

Plug 'joshdick/onedark.vim'
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'mhinz/vim-startify'
Plug 'Yggdroot/indentLine'
Plug 'junegunn/goyo.vim'
Plug 'kjwon15/vim-transparent'
Plug 'vim-utils/vim-man'
Plug 'liuchengxu/vim-which-key'
Plug 'sheerun/vim-polyglot'
Plug 'tpope/vim-fugitive'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'airblade/vim-gitgutter'

call plug#end()

" ==========================================
" -| mappings |-----------------------------
" ==========================================

let mapleader=" "
nnoremap ; :
inoremap ;; <Esc>
nnoremap <down> ddp
nnoremap <up> ddkP
nnoremap <leader>te :TransparentEnable<CR>
nnoremap <leader>td :TransparentDisable<CR>
nnoremap <leader>f. :source $MYVIMRC<CR>
nnoremap <silent> <leader>pi :PlugInstall<CR>
nnoremap <silent> <leader>pu :PlugUpdate<CR>
nnoremap <silent> <leader>pg :PlugUpgrade<CR>
nnoremap <silent> <leader>pc :PlugClean<CR>
nnoremap <leader>fs :write<CR>
nnoremap <leader>qq :quit<CR>
nnoremap <silent> <leader>bd :bdelete<CR>
nnoremap <silent> <leader> :WhichKey '<Space>'<CR>
nnoremap <silent> <leader>wh :split<CR>
nnoremap <silent> <leader>wv :vsplit<CR>
nnoremap <silent> <C-l> :nohl<CR><C-l>
nnoremap <Leader>o :CtrlP<CR>
nnoremap <Leader>bb :CtrlPBuffer<CR>

" ==========================================
" -| general settings |---------------------
" ==========================================

set listchars=eol:$,tab:>-,trail:~,space:␣
set list
syntax on
set hidden
set noerrorbells
set tabstop=4 softtabstop=4
set shiftwidth=4
set expandtab
set smartindent
set fileencoding=utf-8
set fileencodings=ucs-bom,utf-8,gbk,cp936,latin-1
set fileformat=unix
set fileformats=unix,dos,mac
filetype on
filetype plugin on
filetype plugin indent on
syntax on
set nowrap
set ignorecase
set smartcase
set cursorline
set nocursorcolumn
set incsearch
set noshowmode
set cmdheight=2
set updatetime=300
set shortmess+=c
set signcolumn=yes
set mouse=nv
set timeout
set timeoutlen=500
set ttimeout
filetype on
filetype plugin on
filetype indent on
syntax on
set splitright
set splitbelow
set number relativenumber
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

let g:netrw_banner=0
let g:netrw_browse_split=2
let g:netrw_liststyle=3
let g:netrw_winsize=20

if exists('+termguicolors')
    let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
    let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
    set termguicolors
endif
set background=dark

colorscheme onedark

let g:CtrlSpaceDefaultMappingKey = "<C-space> "
let g:airline#extensions#tabline#enabled=0
let g:airline_theme='onedark'
" let g:airline_symbols_ascii=1
let g:which_key_use_floating_win=0
let g:indentLine_char='┆'

let g:startify_files_number = 5
let g:startify_custom_header = [
\'    //=====================================\\',
\'    ||         :            -`             ||',
\'    ||       .dM:          /Md/.``         ||',
\'    ||       hMMm:         hMMMMMNds-      ||',
\'    ||      hMMMMh-       oNMMMMMMMM.      ||',
\'    ||      -mMMMMMy.      :sdNMNNNm.      ||',
\'    ||       .yNMMMMNs.      .dm:```       ||',
\'    ||         :hMMMMMm+`   .mm-           ||',
\'    ||          .sMMMMMMd/` hM:            ||',
\'    ||        -sdy/+mMMMMMdoMd             ||',
\'    ||       oNM:   `oNMMMMMMm`            ||',
\'    ||      oMMN`     .sNMMMMMh.           ||',
\'    ||      hMMMs       -yMMMMMNo`         ||',
\'    ||      +MMMMy`       :hMMMMMm+        ||',
\'    ||       hMMMMm.       `/dMMMMMy       ||',
\'    ||       `NMMMMm`        `+mMMMM-      ||',
\'    ||        hMMMMM/          `sMMM.      ||',
\'    ||        `NMMMMm`        `+mMMMM-     ||',
\'    ||         hMMMMM/          `sMMM.     ||',
\'    ||       .ohhhhhs`            hm:      ||',
\'    \\=====================================//']
