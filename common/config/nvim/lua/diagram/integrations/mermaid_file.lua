-- Custom integration for standalone .mmd and .mermaid files
local renderers = require("diagram/renderers")

local M = {
	id = "mermaid_file",
	filetypes = { "mmd", "mermaid" },
	renderers = {
		renderers.mermaid,
	},
}

M.query_buffer_diagrams = function(bufnr)
	local buf = bufnr or vim.api.nvim_get_current_buf()
	local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
	local content = table.concat(lines, "\n")

	if content and content ~= "" then
		local line_count = vim.api.nvim_buf_line_count(buf)
		return {
			{
				bufnr = buf,
				renderer_id = "mermaid",
				source = content,
				range = {
					start_row = 0,
					start_col = 0,
					end_row = line_count - 1,
					end_col = 0,
				},
			},
		}
	end
	return {}
end

return M
