return {
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
}
