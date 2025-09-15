#!/usr/bin/python3

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

scripts_dir = Path("/home/rash/.config/scripts")
backup_scripts_dir = scripts_dir / "backup" / "crontab"
status_dir = scripts_dir / "_cache"

script_mapping = {
    "oden": "bkup_oden.py",
    "oldhp": "bkup_oldhp.py",
    "buku": "bkup_buku.py",
    "snapshot-keep": "snapshot_keep_policy.py",
    "take-root-snapshot": "take_root_snapshot.py",
    "take-home-snapshot": "take_home_snapshot.py",
    "take-all-snapshots": "all",
}


def generate_snapshot_name(prefix, date_format="%Y%m%d_%H%M"):
    """Generate snapshot name with timestamp."""
    timestamp = datetime.now().strftime(date_format)
    return f"{prefix}{timestamp}"


additional_args = {
    "take-root-snapshot": [
        "-s",
        generate_snapshot_name("backup_root_"),
    ],
    "take-home-snapshot": [
        "-s", 
        generate_snapshot_name("backup_home_"),
    ]
}


def is_interactive():
    """Check if script is running interactively."""
    return sys.stdout.isatty() and sys.stdin.isatty()


def create_status_file(operation, status="running", progress=0, details=None):
    """Create status file for monitoring."""
    if not status_dir.exists():
        status_dir.mkdir(parents=True, exist_ok=True)

    status_file = status_dir / f"{operation}.status"
    status_data = {
        "operation": operation,
        "status": status,
        "progress": progress,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }

    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        # Use print instead of logger since logger may not be initialized yet
        print(f"Failed to create status file: {e}", file=sys.stderr)


def verify_snapshot_completion(snapshot_path):
    """Verify that a btrfs snapshot completed successfully."""
    try:
        # Check if snapshot is read-only
        result = subprocess.run(['btrfs', 'property', 'get', snapshot_path, 'ro'], 
                              capture_output=True, text=True, check=True)
        if 'ro=true' not in result.stdout:
            return False, "Snapshot is not read-only"
        
        # Check for Received UUID if it's from btrfs send/receive
        result = subprocess.run(['btrfs', 'subvolume', 'show', snapshot_path],
                              capture_output=True, text=True, check=True)
        
        # If we get here without exception, the snapshot exists and is readable
        return True, "Snapshot verification passed"
    except subprocess.CalledProcessError as e:
        return False, f"Verification failed: {e}"


def run_script_with_continue_on_failure(script_name, script_path, args, env, interactive=False):
    """Run script and continue on failure if specified."""
    import logging
    logger = logging.getLogger(__name__)
    operation_name = f"backup_{script_name}"
    
    if interactive:
        print(f"Running {script_name}...")
    
    create_status_file(operation_name, "running", 0)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, *args],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verify snapshot if this is a snapshot operation
        if "snapshot" in script_name and "take" in script_name:
            # Extract snapshot name from args
            snapshot_name = None
            for i, arg in enumerate(args):
                if arg == "-s" and i + 1 < len(args):
                    snapshot_name = args[i + 1]
                    break
            
            if snapshot_name:
                # Both root and home snapshots are stored in /.snapshots
                snapshot_path = f"/.snapshots/{snapshot_name}"
                
                if snapshot_path:
                    verified, verify_msg = verify_snapshot_completion(snapshot_path)
                    if not verified:
                        logger.error(f"Snapshot verification failed for {script_name}: {verify_msg}")
                        create_status_file(operation_name, "failed", 100, {"error": f"Verification failed: {verify_msg}"})
                        if interactive:
                            print(f"Warning: {script_name} verification failed: {verify_msg}")
                        return False, f"Verification failed: {verify_msg}"
                    else:
                        if interactive:
                            print(f"Snapshot verification passed for {script_name}")
        
        create_status_file(operation_name, "completed", 100)
        if interactive:
            print(f"{script_name} completed successfully.")
        logger.info(f"Script {script_name} completed successfully")
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Script failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f": {e.stderr.strip()}"
        
        logger.error(f"Error in {script_name}: {error_msg}")
        create_status_file(operation_name, "failed", 100, {"error": error_msg, "stderr": e.stderr})
        
        if interactive:
            print(f"Error: {script_name} failed with exit code {e.returncode}")
            if e.stderr:
                print(f"Error details: {e.stderr.strip()}")
        
        return False, error_msg


def set_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{env['PYTHONPATH']}:{scripts_dir}"
    else:
        env["PYTHONPATH"] = str(scripts_dir)
    return env


def setup_logging():
    """Setup logging after PYTHONPATH is configured."""
    sys.path.insert(0, str(scripts_dir))
    from _utils import logging_utils
    import logging
    
    # Configure logging
    logging_utils.configure_logging()
    return logging.getLogger(__name__)


def main():
    # Setup logging first
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Run backup scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available scripts:\n"
        + "\n".join(f"  {k} -> {v}" for k, v in script_mapping.items()),
    )
    parser.add_argument(
        "--script",
        choices=list(script_mapping.keys()),
        required=True,
        help="Script to run",
    )
    parser.add_argument(
        "--continue-on-failure", 
        action="store_true",
        help="Continue executing other scripts even if one fails (default behavior)"
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true", 
        help="Stop executing remaining scripts if one fails"
    )
    args = parser.parse_args()

    # Determine failure behavior - default is continue, unless --stop-on-failure is specified
    continue_on_failure = not args.stop_on_failure
    
    interactive = is_interactive()
    env = set_pythonpath()

    # Handle special case for running all snapshots
    if args.script == "take-all-snapshots":
        if interactive:
            print("Starting all snapshots operation...")
        
        create_status_file("backup_all_snapshots", "running", 0)
        
        # Track results
        results = {}
        overall_success = True
        
        # Run root snapshot first
        root_script_path = backup_scripts_dir / script_mapping["take-root-snapshot"]
        success, output = run_script_with_continue_on_failure(
            "take-root-snapshot", 
            root_script_path, 
            additional_args.get("take-root-snapshot", []), 
            env, 
            interactive
        )
        results["root_snapshot"] = {"success": success, "output": output}
        if not success:
            overall_success = False
            if not continue_on_failure:
                logger.error("Root snapshot failed, exiting")
                create_status_file("backup_all_snapshots", "failed", 50, {"failed_at": "root_snapshot"})
                sys.exit(1)
        
        # Update progress
        create_status_file("backup_all_snapshots", "running", 50)
        
        # Run home snapshot second
        home_script_path = backup_scripts_dir / script_mapping["take-home-snapshot"]
        success, output = run_script_with_continue_on_failure(
            "take-home-snapshot", 
            home_script_path, 
            additional_args.get("take-home-snapshot", []), 
            env, 
            interactive
        )
        results["home_snapshot"] = {"success": success, "output": output}
        if not success:
            overall_success = False
            if not continue_on_failure:
                logger.error("Home snapshot failed, exiting")
                create_status_file("backup_all_snapshots", "failed", 100, {"failed_at": "home_snapshot"})
                sys.exit(1)
        
        # Final status update
        if overall_success:
            create_status_file("backup_all_snapshots", "completed", 100, {"results": results})
            if interactive:
                print("All snapshots completed successfully.")
            logger.info("All snapshots completed successfully")
        else:
            failed_ops = [k for k, v in results.items() if not v["success"]]
            create_status_file("backup_all_snapshots", "completed_with_errors", 100, {
                "results": results, 
                "failed_operations": failed_ops
            })
            if interactive:
                print(f"Snapshots completed with errors. Failed: {', '.join(failed_ops)}")
            logger.error(f"Some snapshots failed: {', '.join(failed_ops)}")
            
            if not continue_on_failure:
                sys.exit(1)
        
        return

    # Handle individual script execution
    script_path = backup_scripts_dir / script_mapping[args.script]

    if not script_path.exists():
        error_msg = f"Script file not found: {script_path}"
        logger.error(error_msg)
        if interactive:
            print(f"Error: {error_msg}")
            print(f"Available scripts: {', '.join(script_mapping.keys())}")
        sys.exit(1)

    success, output = run_script_with_continue_on_failure(
        args.script,
        script_path,
        additional_args.get(args.script, []),
        env,
        interactive
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
