return {
  "denialofsandwich/sudo.nvim",
  lazy = true,
  cmd = { "SudoRead", "SudoWrite", "SudoEdit" },
  dependencies = {
    "MunifTanjim/nui.nvim",
  },
  opts = {
    -- optional configuration
    -- commands = true,
  },
}
