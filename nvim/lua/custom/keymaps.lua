--=============================================================================
-- KEYMAPS
--=============================================================================
-- All plugin-specific keymaps are now managed here, not in plugin configs
-- Note: Additional plugin-specific keymaps can be found in their respective plugin configs

--==========================================================================
--                          PLUGIN MAPPINGS
--==========================================================================

-- Which-key group registration (popup organization)
local wk_ok, wk = pcall(require, "which-key")
if wk_ok then
	wk.add({
		{ "<leader><leader>", group = "Quick Actions", mode = { "n", "v" } },
		{ "<leader>a", group = "[A]vante AI", mode = { "n", "v" } },
		{ "<leader>b", group = "[B]uffer Operations", mode = { "n", "v" } },
		{ "<leader>c", group = "[C]laude Code", mode = { "n", "v" } },
		{ "<leader>f", group = "[F]ind", mode = { "n", "v" } },
		{ "<leader>g", group = "[G]it", mode = { "n", "v" } },
		{ "<leader>j", group = "[J]ust Explore", mode = { "n", "v" } },
		{ "<leader>s", group = "[S]earch", mode = { "n", "v" } },
		{ "<leader>t", group = "[T]oggle", mode = { "n", "v" } },
		{ "<leader>w", group = "[W]indow", mode = { "n", "v" } },
		{ "<leader>=", group = "Apply format [=]", mode = { "n" } },
		{ "-", group = "Window splits [|]", mode = { "n", "v" } },
	})
end

-- Claude Code (AI plugin)
local claude_mappings = {
	{
		"n",
		"<leader>cc",
		function()
			vim.cmd("ClaudeCode")
		end,
		{ desc = "Open Claude Code" },
	},
	{
		"n",
		"<leader>cn",
		function()
			vim.cmd("ClaudeCode --continue")
		end,
		{ desc = "Continue with Claude Code" },
	},
}

-- Conform.nvim (formatting)
local format_mappings = {
	{
		"n",
		"<leader>=",
		function()
			local ok, conform = pcall(require, "conform")
			if ok then
				conform.format({ async = true, lsp_format = "fallback" })
			end
		end,
		{ desc = "Format buffer [=]" },
	},
}

-- Snacks.nvim explorer (replacing neo-tree)
local snacks_explorer_mappings = {
	{
		"n",
		"<leader>jj",
		function()
			local ok, snacks = pcall(require, "snacks")
			if ok then
				snacks.explorer()
			end
		end,
		{ desc = "Toggle Explorer" },
	},
	{
		"n",
		"<leader>jh",
		function()
			local ok, snacks = pcall(require, "snacks")
			if ok then
				snacks.explorer({ path = vim.fn.expand("%:p:h") })
			end
		end,
		{ desc = "Reveal file in Explorer" },
	},
}

-- File Browser (Telescope extension)
local filebrowser_mappings = {
	{
		"n",
		"<leader>sb",
		function()
			local ok, telescope = pcall(require, "telescope")
			if ok and telescope.extensions and telescope.extensions.file_browser then
				telescope.extensions.file_browser.file_browser({
					hidden = true,
					hide_dotfiles = true,
					mappings = {
						["n"] = {
							h = function()
								local ok2, fb_actions = pcall(require, "telescope")
								if
									ok2
									and fb_actions.extensions
									and fb_actions.extensions.file_browser
									and fb_actions.extensions.file_browser.actions
								then
									fb_actions.extensions.file_browser.actions.goto_parent_dir()
								end
							end,
							l = function()
								local ok2, actions = pcall(require, "telescope.actions")
								if ok2 then
									actions.open_current()
								end
							end,
						},
					},
				})
			end
		end,
		{ desc = "[S]earch with file [B]rowser" },
	},
}

-- Flash.nvim: fast navigation
local flash_mappings = {
	{
		{ "n", "x", "o" },
		"<leader>ff",
		function()
			local ok, flash = pcall(require, "flash")
			if ok then
				flash.jump()
			end
		end,
		{ desc = "Flash jump (fast navigation)" },
	},
}

-- Telescope keymaps (migrated from plugin config)
local telescope_mappings = {
	{
		"n",
		"<leader>sb",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.buffers()
			end
		end,
		{ desc = "[S]earch existing buffers" },
	},
	{
		"n",
		"<leader>sz",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.current_buffer_fuzzy_find(
					require("telescope.themes").get_dropdown({ winblend = 10, previewer = false })
				)
			end
		end,
		{ desc = "[/] Fuzzily search in current buffer" },
	},
	{
		"n",
		"<leader>sr",
		function()
			local ok, ext = pcall(require, "telescope")
			if ok and ext.extensions and ext.extensions.frecency then
				ext.extensions.frecency.frecency({ hidden = true, no_ignore = true })
			end
		end,
		{ desc = "[S]earch F[R]ecent files" },
	},
	{
		"n",
		"<leader>sd",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.diagnostics()
			end
		end,
		{ desc = "[S]earch [D]iagnostics" },
	},
	{
		"n",
		"<leader>sf",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.find_files()
			end
		end,
		{ desc = "[S]earch [F]iles" },
	},
	{
		"n",
		"<leader>sg",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.live_grep()
			end
		end,
		{ desc = "[S]earch by [G]rep" },
	},
	{
		"n",
		"<leader>sh",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.help_tags()
			end
		end,
		{ desc = "[S]earch [H]elp" },
	},
	{
		"n",
		"<leader>sk",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.keymaps()
			end
		end,
		{ desc = "[S]earch [K]eymaps" },
	},
	{
		"n",
		"<leader>sn",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.find_files({ cwd = vim.fn.stdpath("config") })
			end
		end,
		{ desc = "[S]earch [N]eovim files" },
	},
	{
		"n",
		"<leader>s<Enter>",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.resume()
			end
		end,
		{ desc = "[S]earch [R]esume" },
	},
	{
		"n",
		"<leader>ss",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.builtin()
			end
		end,
		{ desc = "[S]earch [S]elect Telescope" },
	},
	{
		"n",
		"<leader>s/",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.live_grep({ grep_open_files = true, prompt_title = "Live Grep in Open Files" })
			end
		end,
		{ desc = "[S]earch [/] in Open Files" },
	},
	{
		"n",
		"<leader>sw",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.grep_string()
			end
		end,
		{ desc = "[S]earch current [W]ord" },
	},
	{
		"n",
		"<leader>s.",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.oldfiles()
			end
		end,
		{ desc = '[S]earch Recent Files ("." for repeat)' },
	},
}

--==========================================================================
--                          CUSTOM KEYMAPS
--==========================================================================

-- Basic movement and operations
local basic_mappings = {
	{ "n", "<Esc>", "<cmd>nohlsearch<CR>", nil },
	{ "t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" } },
}

-- Disable arrow keys in normal mode
local arrow_mappings = {
	{ "n", "<left>", "<cmd>echo 'Use h to move!!'<CR>", { desc = nil } },
	{ "n", "<right>", "<cmd>echo 'Use l to move!!'<CR>", { desc = nil } },
	{ "n", "<up>", "<cmd>echo 'Use k to move!!'<CR>", { desc = nil } },
	{ "n", "<down>", "<cmd>echo 'Use j to move!!'<CR>", { desc = nil } },
}

-- Faster navigation
local fastnav_mappings = {
	{ "n", "<C-j>", "10j", { desc = "Move down 10 times" } },
	{ "v", "<C-j>", "10j", { desc = "Move down 10 times" } },
	{ "n", "<C-k>", "10k", { desc = "Move up 10 times" } },
	{ "v", "<C-k>", "10k", { desc = "Move up 10 times" } },
}

-- Diagnostics
local diagnostic_mappings = {
	{ "n", "<leader>dq", vim.diagnostic.setloclist, { desc = "Open diagnostic [Q]uickfix list" } },
}

-- Select whole document
local selectall_mappings = {
	{ "n", "<leader>%", "ggVG", { noremap = true, desc = "Select entire buffer" } },
}

-- Buffer and Window Management Keybinds

-- Window creation and closing using <leader>-
local window_operations_mappings = {
	-- Window creation (splits)
	{ "n", "-s", "<C-w>s", { desc = "Split window horizontally" } },
	{ "n", "-v", "<C-w>v", { desc = "Split window vertically" } },
	-- Window closing
	{ "n", "-c", "<C-w>c", { desc = "Close current window/split" } },
}

-- Window navigation using Alt+Shift+hjkl
local window_navigation_mappings = {
	{ "n", "<A-S-h>", "<C-w>h", { desc = "Go to left window" } },
	{ "n", "<A-S-j>", "<C-w>j", { desc = "Go to lower window" } },
	{ "n", "<A-S-k>", "<C-w>k", { desc = "Go to upper window" } },
	{ "n", "<A-S-l>", "<C-w>l", { desc = "Go to right window" } },
	{ "n", "<A-S-w>", "<C-w>w", { desc = "Go to next window" } },
}

-- Buffer management keybinds using <leader>b
local buffer_mappings = {
	-- Buffer creation
	{ "n", "<leader>bn", ":enew<CR>", { desc = "Create new buffer" } },
	-- Buffer navigation
	{ "n", "<leader>bj", ":bnext<CR>", { desc = "Next buffer" } },
	{ "n", "<leader>bk", ":bprev<CR>", { desc = "Previous buffer" } },
	{ "n", "<leader>bl", ":blast<CR>", { desc = "Last buffer" } },
	{ "n", "<leader>bf", ":bfirst<CR>", { desc = "First buffer" } },
	-- Buffer closing
	{ "n", "<leader>bc", ":bd<CR>", { desc = "Close buffer completely" } },
	{ "n", "<leader>b!", ":bd!<CR>", { desc = "Force close buffer (ignore unsaved)" } },
	-- Buffer listing
	{ "n", "<leader>bb", ":ls<CR>", { desc = "List all buffers" } },
}

-- Delete to blackhole mappings
local delete_to_blackhole_mappings = {
	{ "n", "D", '"_d', { desc = "Delete to blackhole" } },
	{ "v", "D", '"_d', { desc = "Delete to blackhole" } },
	{ "n", "DD", '"_dd', { desc = "Delete line to blackhole" } },
}

-- =====================
-- Keymap binding section
-- =====================

local function set_keymaps(mappings)
	for _, map in ipairs(mappings) do
		local mode, lhs, rhs, opts = map[1], map[2], map[3], map[4]
		if type(mode) == "table" then
			vim.keymap.set(mode, lhs, rhs, opts or {})
		else
			vim.keymap.set(mode, lhs, rhs, opts or {})
		end
	end
end

set_keymaps(claude_mappings)
set_keymaps(format_mappings)
set_keymaps(snacks_explorer_mappings)
set_keymaps(basic_mappings)
set_keymaps(arrow_mappings)
set_keymaps(fastnav_mappings)
set_keymaps(window_operations_mappings)
set_keymaps(window_navigation_mappings)
set_keymaps(buffer_mappings)
set_keymaps(diagnostic_mappings)
set_keymaps(filebrowser_mappings)
set_keymaps(selectall_mappings)
set_keymaps(flash_mappings)
set_keymaps(telescope_mappings)
set_keymaps(delete_to_blackhole_mappings)

return {}
