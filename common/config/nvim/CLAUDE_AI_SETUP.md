# Claude AI Autocomplete Setup

This Neovim configuration includes AI-powered autocomplete using Claude Haiku.

## Setup Instructions

### 1. Get Your Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key

### 2. Set Environment Variable

Add your API key to your shell configuration:

**For bash** (~/.bashrc):
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**For zsh** (~/.zshrc):
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**For fish** (~/.config/fish/config.fish):
```fish
set -gx ANTHROPIC_API_KEY 'your-api-key-here'
```

### 3. Reload Configuration

```bash
source ~/.bashrc  # or ~/.zshrc or config.fish
```

### 4. Install Plugins

Open Neovim and run:
```vim
:Lazy sync
```

## Usage

Once configured, Claude AI completions will appear automatically as you type alongside your LSP completions.

**Completion Sources (in order of priority):**
1. LSP (Language Servers)
2. Path (file paths)
3. Snippets (LuaSnip)
4. Lazydev (Lua development)
5. Claude AI (AI-powered suggestions)

**Keybindings:**
- `<Tab>` - Accept completion
- `<C-j>` - Next completion
- `<C-k>` - Previous completion
- `<C-space>` - Show/toggle documentation
- `<C-e>` - Hide completion menu

## Configuration

The Claude AI provider is configured in:
- Plugin: `lua/plugins/cmp-ai.lua`
- Integration: `lua/plugins/blink-cmp.lua`

**Current Settings:**
- Model: `claude-3-haiku-20240307`
- Max lines: 100
- Run on every keystroke: No (better performance)
- Notifications: Enabled

## Troubleshooting

### No AI completions appearing

1. Check API key is set: `echo $ANTHROPIC_API_KEY`
2. Check plugin is loaded: `:Lazy` (should see cmp-ai installed)
3. Check for errors: `:messages`

### Rate limiting

If you're seeing rate limit errors, you may need to:
- Upgrade your Anthropic API plan
- Reduce frequency of completions
- Set `run_on_every_keystroke = true` to `false` (already done)

## Cost Considerations

Claude Haiku is Anthropic's fastest and most cost-effective model. However, API usage does incur costs:
- Consider setting a budget limit in the Anthropic Console
- Monitor your usage at https://console.anthropic.com/settings/usage

## Alternative Models

To use a different Claude model, edit `lua/plugins/cmp-ai.lua`:

```lua
provider_options = {
  model = "claude-3-5-sonnet-20241022",  -- More powerful but slower/costly
  -- or
  model = "claude-3-haiku-20240307",     -- Current: Fast and economical
},
```
