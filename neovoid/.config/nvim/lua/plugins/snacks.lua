return {
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
}
