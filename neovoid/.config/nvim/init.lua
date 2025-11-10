-- ██╗      █████╗ ███████╗██╗   ██╗
-- ██║     ██╔══██╗╚══███╔╝╚██╗ ██╔╝
-- ██║     ███████║  ███╔╝  ╚████╔╝
-- ██║     ██╔══██║ ███╔╝    ╚██╔╝
-- ███████╗██║  ██║███████╗   ██║
-- ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\npress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.o.termguicolors = true

require("lazy").setup({
  ui = {
    border = 'rounded'
  },
  spec = { import = 'plugins' },
  checker = { enabled = true },
})

vim.cmd.colorscheme('neopywal')

-- ██╗  ██╗███████╗██╗   ██╗███████╗
-- ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝
-- █████╔╝ █████╗   ╚████╔╝ ███████╗
-- ██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║
-- ██║  ██╗███████╗   ██║   ███████║
-- ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝
-- vim.keymap.del('n', '<CR>')
vim.keymap.set('n', '<esc>', '<cmd>nohl<enter>')
vim.keymap.set('v', '>', '>gv')
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('n', '<leader>fw', '<cmd>w<enter>', { desc = 'write to file' })
vim.keymap.set('n', '<leader>fq', '<cmd>wq<enter>', { desc = 'write to file and quit' })
vim.keymap.set('n', '<leader>qq', '<cmd>q<enter>', { desc = 'quit neovim' })
vim.keymap.set('n', '<leader>qa', '<cmd>q!<enter>', { desc = 'force quit neovim' })

--  ██████╗ ██████╗ ████████╗███████╗
-- ██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝
-- ██║   ██║██████╔╝   ██║   ███████╗
-- ██║   ██║██╔═══╝    ██║   ╚════██║
-- ╚██████╔╝██║        ██║   ███████║
--  ╚═════╝ ╚═╝        ╚═╝   ╚══════╝
vim.g.have_nerd_font = true
vim.o.tabstop = 2
vim.o.softtabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true
vim.o.autochdir = true
vim.o.autoindent = true
vim.o.smartindent = true
vim.o.autoread = true
vim.o.backup = false
vim.o.breakindent = true
vim.o.clipboard = 'unnamedplus'
vim.o.cmdheight = 0
vim.o.cmdwinheight = 7
vim.o.completeopt = 'menuone,preview,popup,noinsert,noselect'
vim.o.confirm = true
vim.o.cursorline = true
vim.o.cursorlineopt = 'line,number'
vim.o.emoji = true
vim.o.guicursor = 'n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50,a:blinkwait700-blinkoff400-blinkon250-Cursor/lCursor,sm:block-blinkwait175-blinkoff150-blinkon175'
vim.o.hlsearch = false
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.incsearch = true
vim.o.hlsearch = true
vim.o.mouse = 'a'
vim.o.mousehide = true
vim.o.mousescroll = 'ver:1,hor:1'
vim.o.number = true
vim.o.numberwidth = 3
vim.o.pumblend = 10
vim.o.relativenumber = true
vim.o.scrolloff = 5
vim.o.sidescrolloff = 5
vim.o.shiftround = true
vim.o.showcmd = false
vim.o.showmode = false
vim.o.signcolumn = 'yes'
vim.o.splitbelow = true
vim.o.splitright = true
vim.o.swapfile = false
vim.o.undofile = true
vim.o.winblend = 10
vim.o.winborder = 'rounded'
vim.o.wrap = false

-- transparent background
vim.cmd [[
highlight Normal guibg=none
highlight NonText guibg=none
highlight Normal ctermbg=none
highlight NonText ctermbg=none
]]

--  █████╗ ██╗   ██╗████████╗ ██████╗
-- ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
-- ███████║██║   ██║   ██║   ██║   ██║
-- ██╔══██║██║   ██║   ██║   ██║   ██║
-- ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
-- ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝
vim.api.nvim_create_autocmd("User", {
  pattern = "SnacksDashboardOpened",
  callback = function(data)
    vim.b[data.buf].miniindentscope_disable = true
  end,
})

vim.api.nvim_create_autocmd("User", {
  pattern = "SnacksDashboardClosed",
  callback = function(data)
    vim.b[data.buf].miniindentscope_disable = false
  end,
})

vim.api.nvim_create_autocmd("User", {
  pattern = "OilActionsPost",
  callback = function(event)
    if event.data.actions.type == "move" then
      Snacks.rename.on_rename_file(event.data.actions.src_url, event.data.actions.dest_url)
    end
  end,
})
