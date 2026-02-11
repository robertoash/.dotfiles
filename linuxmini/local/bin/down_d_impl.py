#!/usr/bin/env python3
"""
Download videos with yt-dlp using a 3-tier fallback strategy with rich progress display.
"""

import argparse
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

console = Console()

YT_DLP_PATH = "/home/rash/.local/bin/yt-dlp"


class DownloadTask:
    """Represents a single download task."""

    def __init__(self, url: str, tier: int, quality: str):
        self.url = url
        self.tier = tier
        self.quality = quality
        self.status = "pending"  # pending, downloading, success, failed
        self.progress_pct = 0.0
        self.speed = ""
        self.eta = ""
        self.size = ""
        self.error = ""


def build_format_string(quality: str) -> str:
    """Build yt-dlp format string based on quality."""
    if quality == "bestvideo+bestaudio/best":
        return quality

    quality_map = {
        "720": "bestvideo[height=720]+bestaudio/best[height=720]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "1080": "bestvideo[height=1080]+bestaudio/best[height=1080]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "1440": "bestvideo[height=1440]+bestaudio/best[height=1440]/bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
        "2160": "bestvideo[height=2160]+bestaudio/best[height=2160]/bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
    }
    return quality_map.get(quality, quality)


def parse_progress_line(line: str) -> Tuple[Optional[float], str, str, str]:
    """Parse yt-dlp/axel progress line and extract percentage, speed, ETA, size."""
    import re

    # yt-dlp format: [download]  26.7% of  430.74MiB at  296.05KiB/s ETA 18:12
    yt_dlp_match = re.search(
        r"\[download\]\s+([0-9.]+)%\s+of\s+([0-9.]+\w+)\s+at\s+([0-9.]+\w+/s)\s+ETA\s+([0-9:]+)",
        line,
    )
    if yt_dlp_match:
        return (
            float(yt_dlp_match.group(1)),
            yt_dlp_match.group(3),
            yt_dlp_match.group(4),
            yt_dlp_match.group(2),
        )

    # Axel format: [ 26%]  .......... [ 12.3MB/s] [ETA: 01:23]
    axel_match = re.search(r"\[\s*([0-9]+)%\].*\[\s*([0-9.]+\w+/s)\].*ETA:\s*([0-9:]+)", line)
    if axel_match:
        return (float(axel_match.group(1)), axel_match.group(2), axel_match.group(3), "")

    # Try simpler percentage match
    pct_match = re.search(r"([0-9.]+)%", line)
    if pct_match:
        return (float(pct_match.group(1)), "", "", "")

    return (None, "", "", "")


def download_with_progress(
    task: DownloadTask, cmd: List[str], tmpdir: Path, task_id: str,
    height_file: Optional[Path] = None,
) -> bool:
    """Run download command and update task progress."""
    log_file = tmpdir / f"{task_id}.log"
    task.status = "downloading"
    height_resolved = False

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Read output line by line
        with open(log_file, "w") as f:
            for line in process.stdout:
                f.write(line)
                f.flush()

                # Parse progress
                pct, speed, eta, size = parse_progress_line(line)
                if pct is not None:
                    task.progress_pct = pct
                if speed:
                    task.speed = speed
                if eta:
                    task.eta = eta
                if size:
                    task.size = size

                # Read actual resolution from height file written by --print-to-file
                if not height_resolved and height_file and height_file.exists():
                    try:
                        height_val = height_file.read_text().strip()
                        if height_val.isdigit():
                            task.quality = height_val
                            height_resolved = True
                    except OSError:
                        pass

        process.wait()

        # Final check for height file (may have been written after last output line)
        if not height_resolved and height_file and height_file.exists():
            try:
                height_val = height_file.read_text().strip()
                if height_val.isdigit():
                    task.quality = height_val
            except OSError:
                pass

        if process.returncode == 0:
            task.status = "success"
            task.progress_pct = 100.0
            return True
        else:
            task.status = "failed"
            task.error = f"Exit code {process.returncode}"
            return False

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        return False


def build_tier_command(url: str, tier: int, quality: str, height_file: str = "") -> List[str]:
    """Build command for specific tier."""
    format_str = build_format_string(quality)
    base_cmd = [YT_DLP_PATH, "-f", format_str, "--no-abort-on-error", "--add-metadata"]

    if height_file:
        base_cmd.extend(["--print-to-file", "%(height)s", height_file])

    if tier == 1:
        # Fast: axel with 16 connections
        return base_cmd + [
            "--external-downloader",
            "axel",
            "--external-downloader-args",
            "-n 16",
            url,
        ]
    elif tier == 2:
        # Medium: axel + impersonation
        return base_cmd + [
            "--external-downloader",
            "axel",
            "--external-downloader-args",
            "-n 8",
            "--impersonate",
            "Edge:Windows",
            "--cookies-from-browser",
            "firefox",
            url,
        ]
    else:
        # Slow: yt-dlp built-in
        import os

        sp_user = os.environ.get("SP_USER", "")
        sp_pass = os.environ.get("SP_PASS", "")

        cmd = base_cmd + [
            "--concurrent-fragments",
            "4",
            "--legacy-server-connect",
            "--no-check-certificates",
            "--impersonate",
            "Edge:Windows",
            "--cookies-from-browser",
            "firefox",
            "--socket-timeout",
            "30",
            "--retry-sleep",
            "linear=1::2",
            "--fragment-retries",
            "5",
        ]

        if sp_user:
            cmd.extend(["--username", sp_user])
        if sp_pass:
            cmd.extend(["--password", sp_pass])

        cmd.append(url)
        return cmd


def compute_downloaded_size(pct: float, total_size_str: str) -> str:
    """Compute human-readable downloaded size from percentage and total size string.

    Args:
        pct: Download percentage (0-100)
        total_size_str: Total size from yt-dlp (e.g., "430.74MiB", "1.23GiB")

    Returns:
        Downloaded amount in the same unit (e.g., "115.0MiB"), or percentage fallback.
    """
    import re

    if not total_size_str:
        return f"{int(pct)}%" if pct >= 100 else f"{pct:.1f}%"

    match = re.match(r"([0-9.]+)\s*(\w+)", total_size_str)
    if not match:
        return f"{int(pct)}%" if pct >= 100 else f"{pct:.1f}%"

    total_value = float(match.group(1))
    unit = match.group(2)
    downloaded_value = pct / 100.0 * total_value
    return f"{downloaded_value:.1f}{unit}"


def create_progress_table(tasks: Dict[str, DownloadTask], tier: int) -> Table:
    """Create rich table showing download progress."""
    tier_names = {1: "Fast (Axel 16x)", 2: "Fast + Impersonation (Axel 8x)", 3: "Slow (yt-dlp)"}

    table = Table(
        title=f"Tier {tier}: {tier_names[tier]}",
        show_header=True,
        header_style="bold magenta",
        expand=True  # Auto-expand to terminal width
    )
    table.add_column("URL", style="cyan", ratio=3, no_wrap=True)
    table.add_column("Quality", style="bold white", min_width=5, justify="center")
    table.add_column("Status", justify="center", min_width=2, width=6)
    table.add_column("Progress", ratio=2, min_width=25)
    table.add_column("Speed", min_width=10)
    table.add_column("ETA", min_width=7)

    for task_id, task in tasks.items():
        url_short = task.url[:32] + "..." if len(task.url) > 35 else task.url

        # Format quality display
        if task.quality.isdigit():
            quality_display = f"{task.quality}p"
        elif task.status == "downloading":
            quality_display = "..."
        else:
            quality_display = "best"

        if task.status == "success":
            status = "[green]✅[/green]"
            size_label = task.size if task.size else "Done"
            progress = f"[green]███████████████[/green] {size_label}"
        elif task.status == "failed":
            status = "[red]❌[/red]"
            progress = f"[red]{task.error}[/red]"
        elif task.status == "downloading":
            status = "[yellow]⏬[/yellow]"
            bar_width = 15
            filled = int(bar_width * task.progress_pct / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            if task.size:
                downloaded_str = compute_downloaded_size(task.progress_pct, task.size)
                progress = f"[yellow]{bar}[/yellow] {downloaded_str}/{task.size}"
            else:
                pct_str = f"{int(task.progress_pct)}%" if task.progress_pct >= 100 else f"{task.progress_pct:.1f}%"
                progress = f"[yellow]{bar}[/yellow] {pct_str}"
        else:
            status = "[dim]⏳[/dim]"
            progress = "[dim]Waiting...[/dim]"

        table.add_row(
            url_short,
            quality_display,
            status,
            progress,
            task.speed or "-",
            task.eta or "-",
        )

    return table


def download_tier(urls: List[str], tier: int, quality: str) -> Tuple[List[str], List[str]]:
    """Download URLs in parallel for a specific tier."""
    tasks: Dict[str, DownloadTask] = {}
    threads = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Initialize tasks
        for i, url in enumerate(urls):
            task_id = f"task_{tier}_{i}"
            tasks[task_id] = DownloadTask(url, tier, quality)

        # Start download threads
        def download_wrapper(task_id: str, url: str):
            task = tasks[task_id]
            height_file = tmpdir_path / f"{task_id}_height.txt"
            cmd = build_tier_command(url, tier, quality, str(height_file))
            download_with_progress(task, cmd, tmpdir_path, task_id, height_file)

        for i, url in enumerate(urls):
            task_id = f"task_{tier}_{i}"
            thread = threading.Thread(target=download_wrapper, args=(task_id, url))
            thread.start()
            threads.append(thread)

        # Monitor progress with rich
        with Live(create_progress_table(tasks, tier), refresh_per_second=2, console=console) as live:
            while any(t.is_alive() for t in threads):
                live.update(create_progress_table(tasks, tier))
                time.sleep(0.5)

            # Final update
            live.update(create_progress_table(tasks, tier))

        # Wait for all threads
        for thread in threads:
            thread.join()

    # Separate successes and failures
    successes = []
    failures = []
    for i, url in enumerate(urls):
        task_id = f"task_{tier}_{i}"
        if tasks[task_id].status == "success":
            successes.append(url)
        else:
            failures.append(url)

    return successes, failures


def main():
    parser = argparse.ArgumentParser(
        description="Download videos with yt-dlp using a 3-tier fallback strategy"
    )
    parser.add_argument("urls", nargs="+", help="URLs to download")
    parser.add_argument(
        "-q",
        "--quality",
        choices=["720", "1080", "1440", "2160"],
        help="Target video quality",
    )

    args = parser.parse_args()

    quality = "bestvideo+bestaudio/best"
    if args.quality:
        quality = args.quality

    urls_to_download = args.urls
    all_successes = []
    all_failures = []

    # Tier 1: Fast
    console.print("\n[bold blue]Starting Tier 1: Fast Method[/bold blue]")
    tier1_success, tier1_failed = download_tier(urls_to_download, 1, quality)
    all_successes.extend(tier1_success)

    # Tier 2: Medium (retry failures)
    if tier1_failed:
        console.print(
            f"\n[bold yellow]Starting Tier 2: Fast + Impersonation ({len(tier1_failed)} failed)[/bold yellow]"
        )
        tier2_success, tier2_failed = download_tier(tier1_failed, 2, quality)
        all_successes.extend(tier2_success)

        # Tier 3: Slow (retry remaining failures)
        if tier2_failed:
            console.print(
                f"\n[bold red]Starting Tier 3: Slow Method ({len(tier2_failed)} failed)[/bold red]"
            )
            tier3_success, tier3_failed = download_tier(tier2_failed, 3, quality)
            all_successes.extend(tier3_success)
            all_failures = tier3_failed

    # Summary
    console.print("\n[bold]Download Summary[/bold]")
    console.print(f"[green]✅ Successful:[/green] {len(all_successes)}/{len(args.urls)}")
    if all_failures:
        console.print(f"[red]❌ Failed:[/red] {len(all_failures)}")
        for url in all_failures:
            console.print(f"  [red]•[/red] {url}")
        sys.exit(1)
    else:
        console.print("[green]All downloads completed successfully![/green]")


if __name__ == "__main__":
    main()
