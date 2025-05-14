--=============================================================================
-- KEYMAPS
--=============================================================================
-- Note: Additional plugin-specific keymaps can be found in their respective plugin configs
-- Telescope keymaps: <leader>s*, <leader>/, <leader>ff
-- LSP keymaps: gr*, gO, gW, <leader>th
-- Format keymap: <leader>f

-- Basic movement and operations
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")
vim.keymap.set("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" })

-- Disable arrow keys in normal mode
vim.keymap.set("n", "<left>", "<cmd>echo 'Use h to move!!'<CR>")
vim.keymap.set("n", "<right>", "<cmd>echo 'Use l to move!!'<CR>")
vim.keymap.set("n", "<up>", "<cmd>echo 'Use k to move!!'<CR>")
vim.keymap.set("n", "<down>", "<cmd>echo 'Use j to move!!'<CR>")

-- Faster navigation
vim.keymap.set("n", "<C-j>", "10j", { desc = "Move down 10 times" })
vim.keymap.set("n", "<C-k>", "10k", { desc = "Move up 10 times" })

-- Window navigation
vim.keymap.set("n", "<C-s-h>", "<C-w><C-h>", { desc = "Move focus to the left window" })
vim.keymap.set("n", "<C-s-l>", "<C-w><C-l>", { desc = "Move focus to the right window" })
vim.keymap.set("n", "<C-s-j>", "<C-w><C-j>", { desc = "Move focus to the lower window" })
vim.keymap.set("n", "<C-s-k>", "<C-w><C-k>", { desc = "Move focus to the upper window" })

-- Diagnostics
vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, { desc = "Open diagnostic [Q]uickfix list" })

-- File Browser
vim.keymap.set("n", "<leader>sb", ":Telescope file_browser<CR>", { desc = "[S]earch with file [B]rowser" })

-- Buffer operations
vim.keymap.set("n", "<leader>bd", ":bd<CR>", { desc = "[B]uffer [D]elete" })
vim.keymap.set("n", "<leader>bp", ":bp<CR>", { desc = "[B]uffer [P]revious" })
vim.keymap.set("n", "<leader>bn", ":bn<CR>", { desc = "[B]uffer [N]ext" })

-- Select whole document
-- Map <leader>% to grab the ENTIRE document like a document-hungry kraken
vim.keymap.set("n", "<leader>%", "ggVG", { noremap = true, desc = "Select entire buffer" })

-- Return the module
return {}