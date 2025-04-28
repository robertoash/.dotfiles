
-- Tokyonight Deep - Neovim Colorscheme 🌙✨
-- Automatically generated and production-ready.

local M = {}

M.colors = {
  accent = "#8bffff",
  background = "#010111",
  foreground = "#ffffff",
  cursor = "#7dcfff",
  selection_fg = "#ffffff",
  selection_bg = "#515c7e",
  base0 = "#363b54",
  base1 = "#f7768e",
  base2 = "#41a6b5",
  base3 = "#e6c100",
  base4 = "#7aa2f7",
  base5 = "#bb9af7",
  base6 = "#7dcfff",
  base7 = "#b9bdcc",
  bright0 = "#454c6d",
  bright1 = "#ff5f8f",
  bright2 = "#00ffbb",
  bright3 = "#ffee00",
  bright4 = "#82aaff",
  bright5 = "#d5a6ff",
  bright6 = "#8bffff",
  bright7 = "#d0d6e3",
  dark0 = "#1d1d2c",
  dark1 = "#632e3c",
  dark2 = "#1a4760",
  dark3 = "#806b00",
  dark4 = "#354977",
  dark5 = "#4a3e6b",
  dark6 = "#356177",
  dark7 = "#494d5e",
  verydark0 = "#0b0c19",
  verydark1 = "#31182b",
  verydark2 = "#0d2136",
  verydark3 = "#403600",
  verydark4 = "#18204a",
  verydark5 = "#251e4a",
  verydark6 = "#19294c",
  verydark7 = "#25263d",
}

function M.setup()
  local colors = M.colors
  local set_hl = vim.api.nvim_set_hl

  -- Base UI
  set_hl(0, "Normal",          { fg = colors.foreground, bg = colors.background })
  set_hl(0, "Cursor",          { fg = colors.background, bg = colors.cursor })
  set_hl(0, "Visual",          { fg = colors.selection_fg, bg = colors.selection_bg })
  set_hl(0, "CursorLine",      { bg = colors.dark0 })
  set_hl(0, "CursorLineNr",    { fg = colors.accent, bold = true })
  set_hl(0, "LineNr",          { fg = colors.bright0 })
  set_hl(0, "StatusLine",      { fg = colors.foreground, bg = colors.dark4 })
  set_hl(0, "StatusLineNC",    { fg = colors.bright7, bg = colors.dark4 })
  set_hl(0, "VertSplit",       { fg = colors.dark7 })
  set_hl(0, "Pmenu",           { fg = colors.foreground, bg = colors.dark0 })
  set_hl(0, "PmenuSel",        { fg = colors.background, bg = colors.accent })
  set_hl(0, "PmenuThumb",      { bg = colors.bright4 })

  -- Syntax
  set_hl(0, "Comment",         { fg = colors.bright0, italic = true })  -- Brighter for better readability
  set_hl(0, "Constant",        { fg = colors.base5 })
  set_hl(0, "String",          { fg = colors.base2 })
  set_hl(0, "Character",       { fg = colors.base2 })
  set_hl(0, "Number",          { fg = colors.base3 })
  set_hl(0, "Boolean",         { fg = colors.base3 })
  set_hl(0, "Float",           { fg = colors.base3 })
  set_hl(0, "Identifier",      { fg = colors.base4 })
  set_hl(0, "Function",        { fg = colors.bright4 })
  set_hl(0, "Statement",       { fg = colors.base1, bold = true })
  set_hl(0, "Conditional",     { fg = colors.base1 })
  set_hl(0, "Repeat",          { fg = colors.base1 })
  set_hl(0, "Label",           { fg = colors.bright1 })
  set_hl(0, "Operator",        { fg = colors.bright6 })
  set_hl(0, "Keyword",         { fg = colors.bright5, bold = true })
  set_hl(0, "Exception",       { fg = colors.bright1 })
  set_hl(0, "PreProc",         { fg = colors.base6 })
  set_hl(0, "Include",         { fg = colors.bright5 })
  set_hl(0, "Define",          { fg = colors.bright5 })
  set_hl(0, "Macro",           { fg = colors.bright5 })
  set_hl(0, "Type",            { fg = colors.base5 })
  set_hl(0, "StorageClass",    { fg = colors.base5 })
  set_hl(0, "Structure",       { fg = colors.base5 })
  set_hl(0, "Typedef",         { fg = colors.base5 })
  set_hl(0, "Special",         { fg = colors.base4 })
  set_hl(0, "SpecialChar",     { fg = colors.base4 })
  set_hl(0, "Tag",             { fg = colors.bright3 })
  set_hl(0, "Delimiter",       { fg = colors.base7 })  -- 💥 Make delimiters clearly visible but neutral
  set_hl(0, "SpecialComment",  { fg = colors.bright0, italic = true })
  set_hl(0, "Debug",           { fg = colors.bright1 })

  -- Diagnostics
  set_hl(0, "DiagnosticError", { fg = colors.bright1 })
  set_hl(0, "DiagnosticWarn",  { fg = colors.bright3 })
  set_hl(0, "DiagnosticInfo",  { fg = colors.bright4 })
  set_hl(0, "DiagnosticHint",  { fg = colors.bright2 })
  set_hl(0, "DiagnosticOk",    { fg = colors.bright6 })

  -- Treesitter
  set_hl(0, "@variable", { fg = colors.foreground })
  set_hl(0, "@function", { fg = colors.bright4 })
  set_hl(0, "@constant", { fg = colors.base5 })
  set_hl(0, "@keyword",  { fg = colors.bright5 })
  set_hl(0, "@comment",  { fg = colors.bright0, italic = true }) -- consistent with Comment
  set_hl(0, "@type",     { fg = colors.base5 })
  set_hl(0, "@string",   { fg = colors.base2 })
  set_hl(0, "@number",   { fg = colors.base3 })
  set_hl(0, "@boolean",  { fg = colors.base3 })
end

return M
