#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path

KEEP_FIRST = 2
KEEP_LAST = 2
HOME_SYMBOL = "~"


def get_git_repo_name(path: Path) -> str | None:
    try:
        repo_root = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        try:
            remote_url = subprocess.check_output(
                ["git", "-C", str(path), "remote", "get-url", "origin"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()

            # Normalize: extract "author/repo" from SSH or HTTPS
            if "github.com" in remote_url:
                if remote_url.startswith("git@github.com:"):
                    repo_path = remote_url.removeprefix("git@github.com:").removesuffix(
                        ".git"
                    )
                elif remote_url.startswith("https://github.com/"):
                    repo_path = remote_url.removeprefix(
                        "https://github.com/"
                    ).removesuffix(".git")
                else:
                    repo_path = remote_url  # fallback

                author, repo = repo_path.split("/", 1)

                if author == "robertoash":
                    return f" {repo}"  # Leave dot if it's already in repo name
                else:
                    return f" {author}@{repo}"
        except subprocess.CalledProcessError:
            pass

        return f" {Path(repo_root).name}"
    except subprocess.CalledProcessError:
        return None


def compress_path(
    path: str, keep_first: int = KEEP_FIRST, keep_last: int = KEEP_LAST
) -> str:
    path_obj = Path(path).expanduser().resolve()
    home = Path.home().resolve()

    # Replace home with ~
    if home in path_obj.parents or path_obj == home:
        parts = (HOME_SYMBOL,) + path_obj.relative_to(home).parts
    else:
        parts = path_obj.parts

    total_len = len(parts)

    if total_len <= (keep_first + keep_last + 1):
        return "/".join(parts)

    middle = get_git_repo_name(path_obj) or "…"
    compressed = (
        list(parts[:keep_first])
        + ["....."]
        + [middle]
        + ["....."]
        + list(parts[-keep_last:])
    )
    return "/".join(compressed)


if __name__ == "__main__":
    print(compress_path(os.getcwd()))
