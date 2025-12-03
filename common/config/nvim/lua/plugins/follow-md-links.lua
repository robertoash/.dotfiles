-- Autocmd to set up markdown link following
vim.api.nvim_create_autocmd("FileType", {
	pattern = "markdown",
	callback = function()
		-- Custom link following for local files with vertical split and line range support
		vim.keymap.set("n", "<CR>", function()
			local line = vim.api.nvim_get_current_line()
			local col = vim.api.nvim_win_get_cursor(0)[2] + 1

			-- Pattern to match markdown links: [text](url)
			local pattern = "%[([^%]]+)%]%(([^)]+)%)"

			-- Find all markdown links in the line
			local search_start = 1
			while true do
				local text_start, text_end, link_text, url = line:find(pattern, search_start)
				if not text_start then break end

				-- Check if cursor is anywhere within [text](url)
				if col >= text_start and col <= text_end then
					-- Check if this is a web link
					if url:match("^https?://") then
						-- Open web links with the system default browser
						vim.fn.jobstart({"open", url}, {detach = true})
						return
					end

					-- Local file link - parse file path and line numbers
					local file_path = url
					local line_start = nil
					local line_end = nil

					-- Check for line range: file.txt:7-40 or file.txt#L7-L40
					local path_match, start_match, end_match = url:match("^(.-):(%d+)%-(%d+)$")
					if not path_match then
						path_match, start_match, end_match = url:match("^(.-)#L(%d+)%-L(%d+)$")
					end

					if path_match and start_match and end_match then
						file_path = path_match
						line_start = tonumber(start_match)
						line_end = tonumber(end_match)
					else
						-- Check for single line: file.txt:42 or file.txt#L42
						local single_path, single_line = url:match("^(.-):(%d+)$")
						if not single_path then
							single_path, single_line = url:match("^(.-)#L(%d+)$")
						end
						if single_path and single_line then
							file_path = single_path
							line_start = tonumber(single_line)
							line_end = line_start
						end
					end

					-- Expand relative paths from current file's directory
					if not file_path:match("^/") then
						local current_file = vim.api.nvim_buf_get_name(0)
						local current_dir = vim.fn.fnamemodify(current_file, ":h")
						file_path = current_dir .. "/" .. file_path
					end

					-- Open in vertical split
					vim.cmd("vsplit " .. vim.fn.fnameescape(file_path))

					-- Jump to line number/range if specified
					if line_start then
						vim.api.nvim_win_set_cursor(0, {line_start, 0})
						-- Enter visual line mode to select the line(s)
						vim.cmd("normal! V")
						-- If it's a range, extend selection to end line
						if line_end and line_end > line_start then
							vim.api.nvim_win_set_cursor(0, {line_end, 0})
						end
					end

					return
				end

				search_start = text_end + 1
			end

			-- If not on a link, just insert a newline
			vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<CR>", true, false, true), "n", false)
		end, { buffer = true, silent = true, desc = "Follow markdown link" })
	end,
})

-- Return empty table since this is no longer a lazy.nvim plugin spec
return {}
