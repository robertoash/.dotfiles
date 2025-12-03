# cjar 🫙🍪
*Cookie Manager for All Your Cookie Needs™*

Welcome. You've just opened **the Jar** — a warm, terminal-based experience for managing your cookie routine. Inside the jar, you’ll find tools to:

- 🍴 Eat a cookie
- 🤢 Puke a cookie
- 🍽️ Bake a cookie
- 🔒 Close the Jar when you're done

If you don't understand what any of that means... good. You're not supposed to.

## 🧰 Before you eat

We recommend using a fresh plate:

```bash
pipx install cjar
```

## Requirements

### Required tools

`fzf` for cookie interaction
(install via your favorite package pantry)

Example for Arch:

```bash
sudo pacman -S fzf
```

### 🧂 Ingredients You Must Provide Yourself

cjar does not come with ingredients preloaded.
You must source your own kitchenware before opening the jar.

These are the required ingredients:

```bash
CJAR_OVEN=/some/oven
CJAR_LAXATIVE=/some/laxative
DOUGH_STORAGE=/where/you/store/your/dough
DINNER_TABLE=/table/location
JAR_COMPONENTS=/where/you/save/your/recipes
```

If you don't have these ingredients cjar will not bake, serve, or puke.
You must know how to set up your kitchen.

## 🔥 Usage

### 🫙 Traditional Jar Mode
Open the jar:

```bash
cjar
```
You'll be greeted with a small selection of actions. Choose wisely.

| Action | Description |
|--------|-------------|
| 🍴 Eat a Cookie | Begin consuming a cookie |
| 🤢 Puke a Cookie | Remove a cookie from the plate |
| 🍽️ Bake a Cookie | Prepare a new cookie |
| 🔒 Close the Jar | You're done. Walk away. |

After selecting an action, you'll be prompted to name your cookie.

There is no auto-complete. There are no guesses. There are only cookies.

### 🍽️ Table Operations
Set the dinner table:

```bash
cjar table up     # Set the table
cjar table down   # Clear the table
```

The pantry holds your table setup. When the table is cleared, ingredients get sealed away.

### 🥘 Feast Mode 
For the full dining experience:

```bash
cjar feast now    # Eat vanilla + set table
cjar feast done   # Clear table + puke vanilla  
```

This prepares and cleans up the entire feast.

## ☠️ Advanced Usage
Try running:

```bash
cjar
```

Now try it again:

```bash
cjar
```

See the difference?
Of course you don't. That's how good the jar is.

You either know what you're doing or you shouldn't be using the jar.

## 🫙 Cookie Details

The Jar tracks your cookies in:

  - `~/.config/cjar/recipes/<name>.cookie` 📃 (Recipe definitions)
  - `~/.config/cjar/plates/<cookie-name>/` 🍪 (Served cookies)
  - `~/.config/cjar/dough/` → `~/JarStorage/` 🪞 (Mirror to dough storage)
  - `~/JarStorage/<cookie-name>/` 🥖 (Cookie dough)

We won’t tell you what any of that means. You’re either feel at home in the kitchen, or you don't.

## 🔍 Troubleshooting
Eating before baking? That’s not how cookies work.

Puking a cookie you haven’t eaten? Strange, but okay.

Baking the same cookie twice? Overcooked. Too crispy. Reconsider.

## 🔒 Closing the Jar
When you're done:

```bash
cjar
```

Then choose:

```
🔒 Close the Jar
```

No logs. No trails. No crumbs.

Enjoy your cookies.
