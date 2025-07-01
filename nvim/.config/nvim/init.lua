local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

vim.g.mapleader = " "
vim.g.maplocalleader = "\\"
vim.opt.shiftwidth = 2
vim.opt.tabstop = 2
vim.opt.incsearch = true
vim.opt.hlsearch = true

require("lazy").setup({
  spec = {
    -- --------------------
    -- | add plugins here |
    -- --------------------
    {
      "RedsXDD/neopywal.nvim",
      name = "neopywal",
      lazy = false,
      priority = 1000,
      opts = {
        use_palette = "wallust"
      },
    },
    {
      'echasnovski/mini.nvim',
      version = false
    },
  },
  -- colorscheme that will be used when installing plugins.
  install = { colorscheme = { "habamax" } },
  -- automatically check for plugin updates
  checker = { enabled = true },
})

-- ------------------------
-- | plugin setup here |
-- ------------------------
require('mini.icons').setup()
require('mini.statusline').setup()
require('mini.notify').setup()
require('mini.indentscope').setup()
require('mini.cursorword').setup()
require('mini.hipatterns').setup({
  fixme = { pattern = '%f[%w]()FIXME()%f[%W]', group = 'MiniHipatternsFixme' },
  hack  = { pattern = '%f[%w]()HACK()%f[%W]',  group = 'MiniHipatternsHack'  },
  todo  = { pattern = '%f[%w]()TODO()%f[%W]',  group = 'MiniHipatternsTodo'  },
  note  = { pattern = '%f[%w]()NOTE()%f[%W]',  group = 'MiniHipatternsNote'  },
})
require('mini.completion').setup()
require('mini.comment').setup()
require('mini.pairs').setup()
require('mini.files').setup()
require('mini.git').setup()
require('mini.trailspace').setup()
require('mini.keymap').setup()
require('mini.surround').setup()

vim.cmd.colorscheme("neopywal")

