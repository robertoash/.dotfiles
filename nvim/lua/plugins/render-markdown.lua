return {
	"MeanderingProgrammer/render-markdown.nvim",
	dependencies = { 
		"nvim-treesitter/nvim-treesitter", 
		"nvim-tree/nvim-web-devicons" -- or "echasnovski/mini.nvim"
	},
	ft = { "markdown", "Avante" },
	opts = {
		-- Essential settings
		enabled = true,
		file_types = { "markdown", "Avante" },
		render_modes = { "n", "c", "t" }, -- normal, command, and terminal modes (not insert)
		-- Show raw markdown when cursor is on the line
		anti_conceal = {
			enabled = true,
		},
		-- Basic rendering
		heading = {
			enabled = true,
			sign = true,
			width = 'block',  -- Only color the text width, not full line
		},
		code = {
			enabled = true,
			sign = false,
			width = 'block',  -- Only color the text width, not full line
		},
		bullet = {
			enabled = true,
		},
		checkbox = {
			enabled = true,
		},
		pipe_table = {
			enabled = true,
			style = "full",
		},
		quote = {
			enabled = true,
		},
		link = {
			enabled = true,
		},
		dash = {
			-- Render horizontal rules
			enabled = true,
		},
	},
}