return {
  {
    'nvim-treesitter/nvim-treesitter',
    branch = 'master',
    lazy = false,
    build = ':TSUpdate',
    config = function()
      local ts = require('nvim-treesitter.configs')
      ts.setup({
        ensure_installed = { "c", "cpp", "lua", "vim", "vimdoc", "markdown", "markdown_inline", "rust" },
        auto_install = true,
        sync_install = false,
        highlight = { enable = true },
        indent = { enable = true },
        incremental_selection = {
          enable = true,
          keymaps = {
            init_selection = '<enter>',
            node_incremental = '<enter>',
            scope_incremental = false,
            node_decremental = '<backspace>',
          },
        }
      })
    end
  },
  {
    'nvim-treesitter/nvim-treesitter-textobjects',
    dependencies = { 'nvim-treesitter/nvim-treesitter' },
    config = function()
      local ts = require('nvim-treesitter.configs')
      ts.setup({
        textobjects = {
          select = {
            enable = true,
            lookahead = true,
            keymaps = {
              ['af'] = { query = '@function.outer', desc = 'select outer part of function' },
              ['if'] = { query = '@function.inner', desc = 'select inner part of function' },
              ['ac'] = { query = '@class.outer', desc = 'select outer part of class' },
              ['ic'] = { query = '@class.inner', desc = 'select inner part of class' },
              ['as'] = { query = '@local.scope', query_group = 'locals', desc = 'select language scope' },
            },
            selection_modes = {
              ['@parameter.outer'] = 'v',
              ['@function.outer'] = 'V',
              ['@class.outer'] = '<c-v>',
            },
          }
        }
      })
    end
  },
}
