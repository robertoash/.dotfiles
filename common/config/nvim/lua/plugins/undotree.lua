return {
	"mbbill/undotree",
	config = function()
		-- Set up persistent undo
		if vim.fn.has("persistent_undo") == 1 then
			local target_path = vim.fn.expand("~/.local/state/nvim/undo")
			
			-- Create the directory if it doesn't exist
			if vim.fn.isdirectory(target_path) == 0 then
				vim.fn.mkdir(target_path, "p", 0700)
			end
			
			vim.opt.undodir = target_path
			vim.opt.undofile = true
		end
		
		-- Configuration options
		vim.g.undotree_WindowLayout = 1
		vim.g.undotree_ShortIndicators = 0
		vim.g.undotree_SplitWidth = 30
		vim.g.undotree_DiffpanelHeight = 10
		vim.g.undotree_DiffAutoOpen = 1
		vim.g.undotree_SetFocusWhenToggle = 0
		vim.g.undotree_TreeNodeShape = '*'
		vim.g.undotree_TreeVertShape = '|'
		vim.g.undotree_TreeSplitShape = '/'
		vim.g.undotree_TreeReturnShape = '\\'
		vim.g.undotree_DiffCommand = "diff"
		vim.g.undotree_RelativeTimestamp = 1
		vim.g.undotree_HighlightChangedText = 1
		vim.g.undotree_HighlightChangedWithSign = 1
		vim.g.undotree_HighlightSyntaxAdd = "DiffAdd"
		vim.g.undotree_HighlightSyntaxChange = "DiffChange"
		vim.g.undotree_HighlightSyntaxDel = "DiffDelete"
		vim.g.undotree_HelpLine = 1
		vim.g.undotree_CursorLine = 1
	end,
}