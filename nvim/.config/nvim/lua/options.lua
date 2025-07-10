-- Hint: use `:h <option>` to figure out the meaning if needed
vim.o.clipboard = 'unnamedplus'   -- use system clipboard 
vim.o.mouse = 'a'                 -- allow the mouse to be used in Nvim

-- Tab
vim.o.tabstop = 2                 -- number of visual spaces per TAB
vim.o.softtabstop = 2             -- number of spacesin tab when editing
vim.o.shiftwidth = 2              -- insert 4 spaces on a tab
vim.o.expandtab = true            -- tabs are spaces, mainly because of python

-- UI config
vim.o.number = true               -- show absolute number
vim.o.relativenumber = true       -- add numbers to each line on the left side
vim.o.cursorline = true           -- highlight cursor line underneath the cursor horizontally
vim.o.splitbelow = true           -- open new vertical split bottom
vim.o.splitright = true           -- open new horizontal splits right
-- vim.opt.termguicolors = true        -- enabl 24-bit RGB color in the TUI
-- vim.o.showmode = false            -- we are experienced, wo don't need the "-- INSERT --" mode hint

-- Searching
vim.o.incsearch = true            -- search as characters are entered
vim.o.hlsearch = false            -- do not highlight matches
vim.o.ignorecase = true           -- ignore case in searches by default
vim.o.smartcase = true            -- but make it case sensitive if an uppercase is entered

vim.o.undofile = true

vim.cmd.colorscheme("neopywal")
