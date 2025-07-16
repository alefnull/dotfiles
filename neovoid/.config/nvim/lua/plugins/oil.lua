return {
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
}
