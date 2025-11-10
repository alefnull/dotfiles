return {
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
          { "<leader>g", group = "+git" },
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
}
