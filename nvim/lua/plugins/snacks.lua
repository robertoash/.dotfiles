return {
	"folke/snacks.nvim",
	lazy = false,
	priority = 1000,
	config = function()
		require("snacks").setup({
			bigfile = { enabled = true },
			dashboard = { enabled = true },

			lazygit = {
				configure = true,
				config = {
					os = { editPreset = "nvim-remote" },
					gui = { nerdFontsVersion = "3" },
				},
				theme_path = vim.fs.normalize(vim.fn.stdpath("cache") .. "/lazygit-theme.yml"),
				theme = {
					[241] = { fg = "Special" },
					activeBorderColor = { fg = "MatchParen", bold = true },
					cherryPickedCommitBgColor = { fg = "Identifier" },
					cherryPickedCommitFgColor = { fg = "Function" },
					defaultFgColor = { fg = "Normal" },
					inactiveBorderColor = { fg = "FloatBorder" },
					optionsTextColor = { fg = "Function" },
					searchingActiveBorderColor = { fg = "MatchParen", bold = true },
					selectedLineBgColor = { bg = "Visual" },
					unstagedChangesColor = { fg = "DiagnosticError" },
				},
				win = {
					style = "lazygit",
				},
			},
			indent = { enabled = true },
			input = { enabled = true },
			picker = {
				enabled = true,
				hidden = true,
				ignored = true,
				sources = {
					files = {
						hidden = true,
						ignored = true,
					},
					explorer = {
						hidden = true,
						auto_close = false,
						replace_netrw = true,
						ignored = true,
						actions = {
							open_file_and_close = {
								action = function(picker, item)
									if item and vim.fn.isdirectory(item.file) == 0 then
										-- Only close on file open, not directory navigation
										picker:close()
										vim.cmd("edit " .. vim.fn.fnameescape(item.file))
									else
										-- Default action for directories (don't close)
										require("snacks.picker").actions.confirm(picker, item)
									end
								end,
							},
						},
						win = {
							list = {
								keys = {
									["<CR>"] = "open_file_and_close",
									["<C-v>"] = "confirm", -- Keep default for splits
									["<C-x>"] = "confirm", -- Keep default for splits
								},
							},
						},
					},
				},
			},
			notifier = { enabled = true },
			quickfile = { enabled = true },
			scope = { enabled = true },
			scroll = { enabled = true },
			statuscolumn = { enabled = true },
			words = { enabled = true },
		})

				-- Track explorer instance
		local explorer_instance = nil

		-- Auto-open explorer when dashboard is shown
		vim.api.nvim_create_autocmd("User", {
			pattern = "SnacksDashboardOpened",
			callback = function()
				explorer_instance = require("snacks").explorer()
			end,
			desc = "Open explorer when dashboard opens",
		})

		-- Auto-close explorer when opening any file (from Telescope, command line, etc.)
		local debug_file = vim.fn.stdpath("cache") .. "/explorer_debug.log"
		local function log_debug(msg)
			local timestamp = os.date("%H:%M:%S")
			local log_msg = string.format("[%s] %s\n", timestamp, msg)
			-- Append to debug file
			local file = io.open(debug_file, "a")
			if file then
				file:write(log_msg)
				file:close()
			end
		end

		-- Clear debug file on startup
		local file = io.open(debug_file, "w")
		if file then
			file:write("=== Explorer Debug Log Started ===\n")
			file:close()
		end

		vim.api.nvim_create_autocmd("BufEnter", {
			callback = function()
				local buftype = vim.bo.buftype
				local filetype = vim.bo.filetype
				local filename = vim.fn.expand("%:t")
				local filepath = vim.fn.expand("%:p")

				-- Debug: Show what triggered the event
				log_debug(string.format("BufEnter: buftype='%s', filetype='%s', filename='%s', path='%s'",
					buftype, filetype, filename, filepath))

				-- Only close for regular files (not special buffers like terminals, help, etc.)
				if buftype == "" and filetype ~= "dashboard" and filename ~= "" then
					log_debug(string.format("✓ Conditions met - checking for explorer to close (file: %s)", filename))

					-- Try to close explorer using tracked instance
					if explorer_instance then
						log_debug("✓ Explorer instance found")
						local success, result = pcall(function()
							explorer_instance:close()
							explorer_instance = nil
							return true
						end)

						if success then
							log_debug("✅ CLOSED EXPLORER!")
						else
							log_debug("❌ Error closing explorer: " .. tostring(result))
						end
					else
						log_debug("ℹ️ No explorer instance to close")

						-- Fallback: try to close any snacks picker windows
						local success, result = pcall(function()
							local closed_any = false
							for _, win in ipairs(vim.api.nvim_list_wins()) do
								local buf = vim.api.nvim_win_get_buf(win)
								local ft = vim.api.nvim_get_option_value("filetype", { buf = buf })
								if ft == "snacks_picker_list" then
									vim.api.nvim_win_close(win, false)
									closed_any = true
									log_debug("✅ Closed picker window (fallback)")
								end
							end
							return closed_any
						end)

						if not success then
							log_debug("❌ Fallback error: " .. tostring(result))
						end
					end
				else
					log_debug(string.format("✗ Skipped - buftype='%s', filetype='%s', filename='%s'",
						buftype, filetype, filename))
				end
				log_debug("---")
			end,
			desc = "Auto-close explorer when opening files",
		})

		-- Also track when explorer is manually opened
		local original_explorer = require("snacks").explorer
		require("snacks").explorer = function(...)
			explorer_instance = original_explorer(...)
			return explorer_instance
		end

		-- Add command to view debug log
		vim.api.nvim_create_user_command("ExplorerDebugLog", function()
			vim.cmd("edit " .. debug_file)
		end, { desc = "Open explorer debug log" })
	end,
}
