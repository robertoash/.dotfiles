config.load_autoconfig(False)

c.auto_save.session = True
c.editor.command = ["alacritty", "-e", "helix", "{file}:{line}:{column0}"]
c.url.default_page = "about:empty"
c.url.start_pages = ["about:empty"]
c.url.searchengines = {"DEFAULT": "https://search.brave.com/search?q={}&source=desktop"}
c.colors.webpage.darkmode.enabled = True
