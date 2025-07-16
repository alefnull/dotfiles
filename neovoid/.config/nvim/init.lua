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

-- ██████╗ ██╗     ██╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
-- ██╔══██╗██║     ██║   ██║██╔════╝ ██║████╗  ██║██╔════╝
-- ██████╔╝██║     ██║   ██║██║  ███╗██║██╔██╗ ██║███████╗
-- ██╔═══╝ ██║     ██║   ██║██║   ██║██║██║╚██╗██║╚════██║
-- ██║     ███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║███████║
-- ╚═╝     ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝
require("lazy").setup({
  ui = {
    border = 'rounded'
  },
  spec = {
    {
      'RedsXDD/neopywal.nvim',
      name = 'neopywal',
      lazy = false,
      priority = 1000,
      opts = {
        use_palette = 'wallust'
      }
    },
    {
      -- `lazydev` configures Lua LSP for your Neovim config, runtime and plugins
      -- used for completion, annotations and signatures of Neovim apis
      'folke/lazydev.nvim',
      ft = 'lua',
      opts = {
        library = {
          -- Load luvit types when the `vim.uv` word is found
          { path = '${3rd}/luv/library', words = { 'vim%.uv' } },
        },
      },
    },
    { -- Autocompletion
      'saghen/blink.cmp',
      event = 'VimEnter',
      version = '1.*',
      completion = {
        menu = {
          border = 'rounded',
          draw = {
            components = {
              kind_icon = {
                text = function(ctx)
                  local kind_icon, _, _ = require('mini.icons').get('lsp', ctx.kind)
                  return kind_icon
                end,
                -- (optional) use highlights from mini.icons
                highlight = function(ctx)
                  local _, hl, _ = require('mini.icons').get('lsp', ctx.kind)
                  return hl
                end,
              },
              kind = {
                -- (optional) use highlights from mini.icons
                highlight = function(ctx)
                  local _, hl, _ = require('mini.icons').get('lsp', ctx.kind)
                  return hl
                end,
              }
            }
          }
        }
      },
      dependencies = {
        {
          'L3MON4D3/LuaSnip',
          version = '2.*',
          build = (function()
            if vim.fn.has 'win32' == 1 or vim.fn.executable 'make' == 0 then
              return
            end
            return 'make install_jsregexp'
          end)(),
          dependencies = {},
          opts = {},
        },
        'folke/lazydev.nvim',
      },
      --- @module 'blink.cmp'
      --- @type blink.cmp.Config
      opts = {
        keymap = {
          -- 'default' (recommended) for mappings similar to built-in completions
          --   <c-y> to accept ([y]es) the completion.
          --    This will auto-import if your LSP supports it.
          --    This will expand snippets if the LSP sent a snippet.
          -- 'super-tab' for tab to accept
          -- 'enter' for enter to accept
          -- 'none' for no mappings
          -- All presets have the following mappings:
          -- <tab>/<s-tab>: move to right/left of your snippet expansion
          -- <c-space>: Open menu or open docs if already open
          -- <c-n>/<c-p> or <up>/<down>: Select next/previous item
          -- <c-e>: Hide menu
          -- <c-k>: Toggle signature help
          preset = 'enter',
          ['<tab>'] = { 'select_next', 'fallback' },
          ['<s-tab>'] = { 'select_prev', 'fallback' },
        },

        appearance = {
          nerd_font_variant = 'mono',
        },

        completion = {
          documentation = { auto_show = true, auto_show_delay_ms = 500 },
        },

        sources = {
          default = { 'lsp', 'path', 'snippets', 'lazydev' },
          providers = {
            lazydev = { module = 'lazydev.integrations.blink', score_offset = 100 },
          },
        },

        snippets = { preset = 'luasnip' },

        fuzzy = { implementation = 'prefer_rust_with_warning' },

        signature = { enabled = true },
      },
    },
    {
      -- Main LSP Configuration
      'neovim/nvim-lspconfig',
      dependencies = {
        { 'mason-org/mason.nvim', opts = {} },
        'mason-org/mason-lspconfig.nvim',
        'WhoIsSethDaniel/mason-tool-installer.nvim',
        { 'j-hui/fidget.nvim', opts = {} },
      },
      config = function()
        --  This function gets run when an LSP attaches to a particular buffer.
        --    That is to say, every time a new file is opened that is associated with
        --    an lsp (for example, opening `main.rs` is associated with `rust_analyzer`) this
        --    function will be executed to configure the current buffer
        vim.api.nvim_create_autocmd('LspAttach', {
          group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
          callback = function(event)
            local map = function(keys, func, desc, mode)
              mode = mode or 'n'
              vim.keymap.set(mode, keys, func, { buffer = event.buf, desc = 'LSP: ' .. desc })
            end

            map('grn', vim.lsp.buf.rename, '[R]e[n]ame')
            map('gra', vim.lsp.buf.code_action, '[G]oto Code [A]ction', { 'n', 'x' })
            -- map('grr', require('telescope.builtin').lsp_references, '[G]oto [R]eferences')
            -- map('gri', require('telescope.builtin').lsp_implementations, '[G]oto [I]mplementation')
            -- map('grd', require('telescope.builtin').lsp_definitions, '[G]oto [D]efinition')
            map('grD', vim.lsp.buf.declaration, '[G]oto [D]eclaration')
            -- map('gO', require('telescope.builtin').lsp_document_symbols, 'Open Document Symbols')
            -- map('gW', require('telescope.builtin').lsp_dynamic_workspace_symbols, 'Open Workspace Symbols')
            -- map('grt', require('telescope.builtin').lsp_type_definitions, '[G]oto [T]ype Definition')

            -- This function resolves a difference between neovim nightly (version 0.11) and stable (version 0.10)
            ---@param client vim.lsp.Client
            ---@param method vim.lsp.protocol.Method
            ---@param bufnr? integer some lsp support methods only in specific files
            ---@return boolean
            local function client_supports_method(client, method, bufnr)
              if vim.fn.has 'nvim-0.11' == 1 then
                return client:supports_method(method, bufnr)
              else
                return client.supports_method(method, { bufnr = bufnr })
              end
            end

            -- The following two autocommands are used to highlight references of the
            -- word under your cursor when your cursor rests there for a little while.
            --    See `:help CursorHold` for information about when this is executed
            --
            -- When you move your cursor, the highlights will be cleared (the second autocommand).
            local client = vim.lsp.get_client_by_id(event.data.client_id)
            if client and client_supports_method(client, vim.lsp.protocol.Methods.textDocument_documentHighlight, event.buf) then
              local highlight_augroup = vim.api.nvim_create_augroup('kickstart-lsp-highlight', { clear = false })
              vim.api.nvim_create_autocmd({ 'CursorHold', 'CursorHoldI' }, {
                buffer = event.buf,
                group = highlight_augroup,
                callback = vim.lsp.buf.document_highlight,
              })

              vim.api.nvim_create_autocmd({ 'CursorMoved', 'CursorMovedI' }, {
                buffer = event.buf,
                group = highlight_augroup,
                callback = vim.lsp.buf.clear_references,
              })

              vim.api.nvim_create_autocmd('LspDetach', {
                group = vim.api.nvim_create_augroup('kickstart-lsp-detach', { clear = true }),
                callback = function(event2)
                  vim.lsp.buf.clear_references()
                  vim.api.nvim_clear_autocmds { group = 'kickstart-lsp-highlight', buffer = event2.buf }
                end,
              })
            end

            -- The following code creates a keymap to toggle inlay hints in your
            -- code, if the language server you are using supports them
            --
            -- This may be unwanted, since they displace some of your code
            if client and client_supports_method(client, vim.lsp.protocol.Methods.textDocument_inlayHint, event.buf) then
              map('<leader>th', function()
                vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled { bufnr = event.buf })
              end, '[T]oggle Inlay [H]ints')
            end
          end,
        })

        vim.diagnostic.config {
          severity_sort = true,
          float = { border = 'rounded', source = 'if_many' },
          underline = { severity = vim.diagnostic.severity.ERROR },
          signs = vim.g.have_nerd_font and {
            text = {
              [vim.diagnostic.severity.ERROR] = '󰅚 ',
              [vim.diagnostic.severity.WARN] = '󰀪 ',
              [vim.diagnostic.severity.INFO] = '󰋽 ',
              [vim.diagnostic.severity.HINT] = '󰌶 ',
            },
          } or {},
          virtual_text = {
            source = 'if_many',
            spacing = 2,
            format = function(diagnostic)
              local diagnostic_message = {
                [vim.diagnostic.severity.ERROR] = diagnostic.message,
                [vim.diagnostic.severity.WARN] = diagnostic.message,
                [vim.diagnostic.severity.INFO] = diagnostic.message,
                [vim.diagnostic.severity.HINT] = diagnostic.message,
              }
              return diagnostic_message[diagnostic.severity]
            end,
          },
        }

        local capabilities = require('blink.cmp').get_lsp_capabilities()

        local servers = {
          clangd = {},
          gopls = {},
          pyright = {},
          rust_analyzer = {},
          lua_ls = {
            settings = {
              Lua = {
                diagnostics = {
                  disable = {
                    'missing-fields',
                    'trailing-space',
                    'redefined-local',
                    'redefined-label'
                  }
                },
                completion = {
                  callSnippet = 'Replace',
                },
              },
            },
          },
        }

        local ensure_installed = vim.tbl_keys(servers or {})
        vim.list_extend(ensure_installed, {
          'stylua', -- Used to format Lua code
        })
        require('mason-tool-installer').setup { ensure_installed = ensure_installed }

        require('mason-lspconfig').setup {
          ensure_installed = {}, -- explicitly set to an empty table (Kickstart populates installs via mason-tool-installer)
          automatic_installation = false,
          handlers = {
            function(server_name)
              local server = servers[server_name] or {}
              -- This handles overriding only values explicitly passed
              -- by the server configuration above. Useful when disabling
              -- certain features of an LSP (for example, turning off formatting for ts_ls)
              server.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server.capabilities or {})
              require('lspconfig')[server_name].setup(server)
            end,
          },
        }
      end,
    },
    {
      'echasnovski/mini.nvim',
      config = function()
        require('mini.basics').setup()
        require('mini.ai').setup()
        require('mini.cursorword').setup()
        require('mini.surround').setup()
        require('mini.indentscope').setup()
        require('mini.pairs').setup()
        require('mini.snippets').setup()
        require('mini.icons').setup()
        require('mini.statusline').setup()
        require('mini.tabline').setup()
      end
    },
    {
      'folke/which-key.nvim',
      event = 'VeryLazy',
      opts = {
        preset = "helix",
        show_help = false,
        win = {
          width = { min = 1, max = 80 },
          height = { min = 1, max = 10 },
        },
        spec = {
          {
            mode = { "n", "v" },
            { "<leader>p", group = "+pick" },
            { "<leader>f", group = "+file" },
            { "<leader>q", group = "+quit" },
            {
              "<leader>b",
              group = "buffer",
              expand = function()
                return require("which-key.extras").expand.buf()
              end,
            },
            {
              "<leader>w",
              group = "windows",
              proxy = "<c-w>",
              expand = function()
                return require("which-key.extras").expand.win()
              end,
            },
          },
        },
      },
    },
    -- {
    --   'nvim-telescope/telescope.nvim', tag = '0.1.8',
    --   dependencies = { 'nvim-lua/plenary.nvim' },
    --   config = function()
    --     local builtin = require('telescope.builtin')
    --     vim.keymap.set('n', '<leader>tf', builtin.find_files, { desc = 'telescope: files' })
    --     vim.keymap.set('n', '<leader>tg', builtin.live_grep, { desc = 'telescope: grep' })
    --     vim.keymap.set('n', '<leader>tb', builtin.buffers, { desc = 'telescope: buffers' })
    --     vim.keymap.set('n', '<leader>th', builtin.help_tags, { desc = 'telescope: help tags' })
    --   end
    -- },
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
    {
      'stevearc/oil.nvim',
      keys = {
        { '<leader>e', '<cmd>Oil --float --preview<enter>', { desc = 'toggle file explorer' } }
      },
      opts = {
        default_file_explorer = true,
        columns = {
          'icon',
          'type',
          'permissions',
          'size',
          'mtime',
        },
        skip_confirm_for_simple_edits = true,
        keymaps = {
          ["g?"] = { "actions.show_help", mode = "n" },
          ["<enter>"] = "actions.select",
          ["<C-s>"] = { "actions.select", opts = { vertical = true } },
          ["<C-h>"] = { "actions.select", opts = { horizontal = true } },
          ["<C-t>"] = { "actions.select", opts = { tab = true } },
          ["<C-p>"] = "actions.preview",
          ["<esc>"] = { "actions.close", mode = "n" },
          ["<C-l>"] = "actions.refresh",
          ["-"] = { "actions.parent", mode = "n" },
          ["_"] = { "actions.open_cwd", mode = "n" },
          ["`"] = { "actions.cd", mode = "n" },
          ["~"] = { "actions.cd", opts = { scope = "tab" }, mode = "n" },
          ["gs"] = { "actions.change_sort", mode = "n" },
          ["gx"] = "actions.open_external",
          ["g."] = { "actions.toggle_hidden", mode = "n" },
          ["g\\"] = { "actions.toggle_trash", mode = "n" },
        },
        use_default_keymaps = true,
        view_options = {
          show_hidden = true,
          case_insensitive = true,
          sort = {
            { 'type', 'asc' },
            { 'name', 'asc' },
            { 'size', 'desc' },
          },
        },
        float = {
          padding = 2,
          max_width = 150,
          max_height = 30,
          border = "rounded",
          win_options = {
            winblend = 10,
          },
          preview_split = "auto",
        },
        preview_win = {
          update_on_cursor_moved = true,
          preview_method = "fast_scratch",
          win_options = {
            winblend = 10,
          },
        },
        confirmation = {
          max_width = 0.9,
          min_width = { 40, 0.4 },
          max_height = 0.9,
          min_height = { 5, 0.1 },
          border = "rounded",
          win_options = {
            winblend = 10,
          },
        },
        progress = {
          max_width = 0.9,
          min_width = { 40, 0.4 },
          max_height = { 10, 0.9 },
          min_height = { 5, 0.1 },
          border = "rounded",
          minimized_border = "none",
          win_options = {
            winblend = 10,
          },
        },
        ssh = {
          border = "rounded",
        },
        keymaps_help = {
          border = "rounded",
        },
      },
      dependencies = { { "echasnovski/mini.icons", opts = {} } },
      lazy = false,
    },
    {
      'folke/snacks.nvim',
      priority = 1000,
      lazy = false,
      keys = {
        { '<leader>lg', '<cmd>lua Snacks.lazygit()<enter>', { desc = 'open lazygit' } },
        { '<leader>pf', '<cmd>lua Snacks.picker.files()<enter>', { desc = 'pick files' } },
        { '<leader>pb', '<cmd>lua Snacks.picker.buffers()<enter>', { desc = 'pick buffers' } },
      },
      opts = {
        bigfile = { enbaled = true },
        picker = { enabled = true },
        notifier = { enabled = true },
        quickfile = { enabled = true },
        lazygit = { enabled = true },
        input = { enabled = true,
          icon = " ",
          icon_hl = "SnacksInputIcon",
          icon_pos = "left",
          prompt_pos = "title",
          win = { style = "input" },
          expand = true,
        },
        dashboard = {
          enabled = true,
          preset = {
            header = [[
███╗   ██╗███████╗ ██████╗ ██╗   ██╗ ██████╗ ██╗██████╗
████╗  ██║██╔════╝██╔═══██╗██║   ██║██╔═══██╗██║██╔══██╗
██╔██╗ ██║█████╗  ██║   ██║██║   ██║██║   ██║██║██║  ██║
██║╚██╗██║██╔══╝  ██║   ██║╚██╗ ██╔╝██║   ██║██║██║  ██║
██║ ╚████║███████╗╚██████╔╝ ╚████╔╝ ╚██████╔╝██║██████╔╝
╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═══╝   ╚═════╝ ╚═╝╚═════╝]]
          }
        },
        scroll = {
          enabled = true,
          animate = {
            duration = { step = 10, total = 150 },
            easing = "linear",
          },
        },
      },
    },
  },
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
vim.o.termguicolors = true
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

--  ██████╗███╗   ███╗██████╗ ███████╗
-- ██╔════╝████╗ ████║██╔══██╗██╔════╝
-- ██║     ██╔████╔██║██║  ██║███████╗
-- ██║     ██║╚██╔╝██║██║  ██║╚════██║
-- ╚██████╗██║ ╚═╝ ██║██████╔╝███████║
--  ╚═════╝╚═╝     ╚═╝╚═════╝ ╚══════╝
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
