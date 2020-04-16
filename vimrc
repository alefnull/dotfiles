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

Plug 'preservim/nerdcommenter'
Plug 'joshdick/onedark.vim'
Plug 'itchyny/lightline.vim'
Plug 'mhinz/vim-startify'
Plug 'junegunn/goyo.vim'
Plug 'kjwon15/vim-transparent'
Plug 'vim-utils/vim-man'
Plug 'liuchengxu/vim-which-key'
Plug 'sheerun/vim-polyglot'
Plug 'tpope/vim-fugitive'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'airblade/vim-gitgutter'
Plug 'ryanoasis/vim-devicons'
Plug 'vim-syntastic/syntastic'

call plug#end()

" ==========================================
" -| mappings |-----------------------------
" ==========================================

let mapleader=" "
nnoremap <leader>ev :vsplit $MYVIMRC<CR>
nnoremap ; :
inoremap jk <esc>
inoremap <left> <nop>
inoremap <down> <nop>
inoremap <up> <nop>
inoremap <right> <nop>
nnoremap <left> <nop>
nnoremap <down> ddp
nnoremap <up> ddkP
nnoremap <right> <nop>
nnoremap dc ddO
nnoremap <silent> <leader>zz :Goyo<CR>
nnoremap <leader>te :TransparentEnable<CR>
nnoremap <leader>td :TransparentDisable<CR>
nnoremap <silent> <leader>pi :PlugInstall<CR>
nnoremap <silent> <leader>pu :PlugUpdate<CR>
nnoremap <silent> <leader>pg :PlugUpgrade<CR>
nnoremap <silent> <leader>pc :PlugClean<CR>
nnoremap <leader>fs :write<CR>
nnoremap <leader>f. :source $MYVIMRC<CR>
nnoremap <leader>qq :quit<CR>
nnoremap <silent> <leader>bd :bdelete<CR>
nnoremap <silent> <leader> :WhichKey '<Space>'<CR>
nnoremap <silent> <leader>wh :split<CR>
nnoremap <silent> <leader>wv :vsplit<CR>
nnoremap <silent> <c-l> :nohl<CR><c-l>
nnoremap <Leader>o :CtrlP<CR>
nnoremap <Leader>bb :CtrlPBuffer<CR>
nnoremap <leader>ll :set list!<CR>
nnoremap <leader>hc :helpclose<CR>

" ==========================================
" -| general settings |---------------------
" ==========================================

set laststatus=2
set cmdheight=1
set nospell
set showmatch
set visualbell
set encoding=utf-8
set listchars=eol:¬,tab:▸\ ,extends:›,precedes:‹,space:·,trail:~
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
filetype off
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
set showtabline=2
set signcolumn=yes
set mouse=nv
set timeout
set timeoutlen=500
set ttimeout
filetype off
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

set background=dark
colorscheme onedark

let g:netrw_banner=0
let g:netrw_browse_split=2
let g:netrw_liststyle=3
let g:netrw_winsize=20

let g:goyo_width='65%'
let g:goyo_height='85%'

set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*
let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_sh_shellcheck_args = "-x"

if exists('+termguicolors')
    let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
    let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
    set termguicolors
endif

let g:lightline = {
            \ 'active': {
            \   'left': [ [ 'mode', 'paste', 'fugitive' ],
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
            \   'fugitive': 'LightlineFugitive',
            \   'gitbranch': 'FugitiveHead',
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
            \ 'separator': { 'left': '', 'right': '' },
            \ 'subseparator': { 'left': '', 'right': '' },
            \ 'tab': {
            \   'active': [ 'tabnum', 'filename', 'modified' ]
            \ },
            \ }

let g:NERDSpaceDelims=1
let g:NERDCommentEmptyLines=1
let g:NERDTrimTrailingWhitespace=1
let g:NERDToggleCheckAllLines=1

let g:which_key_use_floating_win=0

let g:startify_files_number = 5
let g:startify_custom_header = 'startify#center(g:ascii)'
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
