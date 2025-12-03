import os
import shlex
import subprocess
from pathlib import Path

# Load pantry secrets
JAR_COMPONENTS = Path(os.getenv("JAR_COMPONENTS", Path.home() / ".config" / "cjar"))
RECIPE_PAGES = JAR_COMPONENTS / "recipes"
COOKIE_SUFFIX = ".cookie"
DOUGH_STORAGE = Path(os.getenv("DOUGH_STORAGE", Path.home() / "JarStorage"))
DINNER_TABLE = Path(os.getenv("DINNER_TABLE", JAR_COMPONENTS / "plates"))
_oven = os.getenv("CJAR_OVEN")
_laxative = os.getenv("CJAR_LAXATIVE")

if not _oven:
    raise RuntimeError("❌ CJAR_OVEN is not set. Please specify your oven in .env.")
if not _laxative:
    raise RuntimeError("❌ CJAR_LAXATIVE is not set. The jar cannot puke without it.")

# Now we know these are strings, not None
OVEN: str = _oven
LAXATIVE: str = _laxative

# Create symlink for dough storage if it doesn't exist
DOUGH_SYMLINK = JAR_COMPONENTS / "dough"
if not DOUGH_SYMLINK.exists():
    JAR_COMPONENTS.mkdir(parents=True, exist_ok=True)
    try:
        DOUGH_SYMLINK.symlink_to(DOUGH_STORAGE)
    except (OSError, FileExistsError):
        pass  # Symlink might already exist or we don't have permissions


def get_cookie_recipe(cookie_name: str) -> dict:
    recipe_file = RECIPE_PAGES / f"{cookie_name}{COOKIE_SUFFIX}"
    if not recipe_file.exists():
        raise FileNotFoundError(f"🍪 Recipe for '{cookie_name}' not found in the jar.")
    lines = recipe_file.read_text().splitlines()
    recipe = dict(line.split("=", 1) for line in lines if "=" in line)
    if recipe.get("cookie_name") != cookie_name:
        raise ValueError(
            f"🍪 Recipe mismatch: expected cookie_name={cookie_name}, "
            f"got cookie_name={recipe.get('cookie_name')}"
        )
    return recipe


def bake_cookie(cookie_name: str) -> None:
    RECIPE_PAGES.mkdir(parents=True, exist_ok=True)
    dough_path = DOUGH_STORAGE / cookie_name
    plate_path = DINNER_TABLE / cookie_name
    if (RECIPE_PAGES / f"{cookie_name}{COOKIE_SUFFIX}").exists():
        raise FileExistsError("🍪 Already exists in the jar.")
    if dough_path.exists():
        raise FileExistsError("🚫 Something's already in the oven.")
    if plate_path.exists():
        raise FileExistsError("🚫 There's already a plate ready.")

    dough_path.mkdir(parents=True)
    plate_path.mkdir(parents=True)
    subprocess.run(shlex.split(OVEN) + ["-init", str(dough_path)], check=True)

    # Build simple recipe
    recipe_lines = [
        f"cookie_name={cookie_name}",
        f"plate={plate_path}",
        f"dough_container={dough_path}",
    ]

    recipe = "\n".join(recipe_lines)
    (RECIPE_PAGES / f"{cookie_name}{COOKIE_SUFFIX}").write_text(recipe)


def eat_cookie(cookie_name: str) -> None:
    """Mount a cookie"""
    recipe = get_cookie_recipe(cookie_name)
    subprocess.run(
        shlex.split(OVEN) + [recipe["dough_container"], recipe["plate"], "-o", "allow_other"], check=True
    )


def puke_cookie(cookie_name: str) -> None:
    """Unmount a cookie"""
    recipe = get_cookie_recipe(cookie_name)
    subprocess.run(shlex.split(LAXATIVE) + [recipe["plate"]], check=True)


def get_all_cookies() -> list[str]:
    """Get all registered cookie names."""
    if not RECIPE_PAGES.exists():
        return []
    cookies = []
    for recipe_file in RECIPE_PAGES.glob(f"*{COOKIE_SUFFIX}"):
        cookie_name = recipe_file.stem  # Remove .cookie extension
        cookies.append(cookie_name)
    return sorted(cookies)


def get_sweet_cookies() -> list[str]:
    """Get all sweet cookies (those with sweet=true in their recipe)."""
    if not RECIPE_PAGES.exists():
        return []
    sweet_cookies = []
    for recipe_file in RECIPE_PAGES.glob(f"*{COOKIE_SUFFIX}"):
        try:
            lines = recipe_file.read_text().splitlines()
            recipe = dict(line.split("=", 1) for line in lines if "=" in line)
            if recipe.get("sweet", "").lower() == "true":
                cookie_name = recipe_file.stem
                sweet_cookies.append(cookie_name)
        except Exception:
            # Skip malformed recipe files
            continue
    return sorted(sweet_cookies)
