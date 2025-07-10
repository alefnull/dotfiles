local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
    local lazyrepo = "https://github.com/folke/lazy.nvim.git"
    local out = vim.fn.system({"git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath})
    if vim.v.shell_error ~= 0 then
        vim.api.nvim_echo({{"Failed to clone lazy.nvim:\n", "ErrorMsg"}, {out, "WarningMsg"},
                           {"\nPress any key to exit..."}}, true, {})
        vim.fn.getchar()
        os.exit(1)
    end
end
vim.opt.rtp:prepend(lazypath)

vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

require("lazy").setup({
    spec = { -- ------------
    -- | neopywal |
    -- ------------
    {
        "RedsXDD/neopywal.nvim",
        name = "neopywal",
        lazy = false,
        priority = 1000,
        opts = {
            use_palette = "wallust"
        }
    }, -- ------------
    -- | mini.nvim |
    -- ------------
    {
        'echasnovski/mini.nvim',
        version = false
    }, -- ---------------------
    -- | blink completions |
    -- ---------------------
    {
        "saghen/blink.cmp",
        -- optional: provides snippets for the snippet source
        dependencies = {"rafamadriz/friendly-snippets"},

        -- Use a release tag to download pre-built binaries
        version = "*",
        -- AND/OR build from source, requires nightly: https://rust-lang.github.io/rustup/concepts/channels.html#working-with-nightly-rust
        -- build = 'cargo build --release',
        -- If you use nix, you can build from source using the latest nightly rust with:
        -- build = 'nix run .#build-plugin',

        opts = {
            -- 'default' (recommended) for mappings similar to built-in completions (C-y to accept)
            -- 'super-tab' for mappings similar to VSCode (tab to accept)
            -- 'enter' for enter to accept
            -- 'none' for no mappings
            --
            -- All presets have the following mappings:
            -- C-space: Open menu or open docs if already open
            -- C-n/C-p or Up/Down: Select next/previous item
            -- C-e: Hide menu
            -- C-k: Toggle signature help (if signature.enabled = true)
            --
            -- See :h blink-cmp-config-keymap for defining your own keymap
            keymap = {
                -- Each keymap may be a list of commands and/or functions
                preset = "enter",
                -- Select completions
                ["<Up>"] = {"select_prev", "fallback"},
                ["<Down>"] = {"select_next", "fallback"},
                ["<C-n>"] = {"select_next", "fallback"},
                ["<C-p>"] = {"select_prev", "fallback"},
                -- Scroll documentation
                ["<C-b>"] = {"scroll_documentation_up", "fallback"},
                ["<C-f>"] = {"scroll_documentation_down", "fallback"},
                -- Show/hide signature
                ["<C-k>"] = {"show_signature", "hide_signature", "fallback"}
            },

            appearance = {
                -- 'mono' (default) for 'Nerd Font Mono' or 'normal' for 'Nerd Font'
                -- Adjusts spacing to ensure icons are aligned
                nerd_font_variant = "mono"
            },

            sources = {
                -- `lsp`, `buffer`, `snippets`, `path`, and `omni` are built-in
                -- so you don't need to define them in `sources.providers`
                default = {"lsp", "path", "snippets"}

                -- Sources are configured via the sources.providers table
            },

            -- (Default) Rust fuzzy matcher for typo resistance and significantly better performance
            -- You may use a lua implementation instead by using `implementation = "lua"` or fallback to the lua implementation,
            -- when the Rust fuzzy matcher is not available, by using `implementation = "prefer_rust"`
            --
            -- See the fuzzy documentation for more information
            fuzzy = {
                implementation = "prefer_rust_with_warning"
            },
            completion = {
                -- The keyword should only match against the text before
                keyword = {
                    range = "prefix"
                },
                menu = {
                    -- Use treesitter to highlight the label text for the given list of sources
                    draw = {
                        treesitter = {"lsp"}
                    }
                },
                -- Show completions after typing a trigger character, defined by the source
                trigger = {
                    show_on_trigger_character = true
                },
                documentation = {
                    -- Show documentation automatically
                    auto_show = true
                }
            },

            -- Signature help when tying
            signature = {
                enabled = true
            }
        },
        opts_extend = {"sources.default"}
    }, -- -------------
    -- | LSP/Mason |
    -- -------------
    {
        "mason-org/mason.nvim",
        opts = {}
    }, {
        "mason-org/mason-lspconfig.nvim",
        dependencies = {"mason-org/mason.nvim", "neovim/nvim-lspconfig"},
        opts = {
            ensure_installed = {"pylsp"}
        }
    }, -- -------------
    -- | lspconfig |
    -- -------------
    {
        "neovim/nvim-lspconfig",
        config = function()
            local lspconfig = require("lspconfig")

            lspconfig.pylsp.setup({})
        end
    } -- ---------------------
    -- | NEXT PLUGINS HERE |
    -- ---------------------
    -- {
    -- }
    },
    -- colorscheme that will be used when installing plugins.
    install = {
        colorscheme = {"habamax"}
    },
    -- automatically check for plugin updates
    checker = {
        enabled = true
    }
})

require('mini.icons').setup()
require('mini.statusline').setup()
require('mini.indentscope').setup()
require('mini.cursorword').setup()
require('mini.completion').setup()
require('mini.comment').setup()
require('mini.pairs').setup()
require('mini.files').setup()
require('mini.git').setup()
require('mini.trailspace').setup()
require('mini.keymap').setup()
require('mini.surround').setup()
