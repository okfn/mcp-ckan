#!/usr/bin/env python3
"""
Fetch remote tool repositories declared in tool_sources.yaml

Clones or updates git repos into remote_tools/<name>/ and checks out
the specified ref. Removes repos no longer present in the manifest.

Usage:
    python scripts/fetch_remote_tools.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "tool_sources.yaml"
REMOTE_DIR = PROJECT_ROOT / "remote_tools"


def run_git(args, cwd=None, ssh_key=None):
    """Run a git command and return (success, output).

    If ssh_key is provided, sets GIT_SSH_COMMAND so git uses that
    specific private key for authentication.
    """
    env = None
    if ssh_key:
        env = {
            **subprocess.os.environ,
            "GIT_SSH_COMMAND": f"ssh -i {ssh_key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new",
        }

    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def clone_repo(name, repo_url, ref, target_dir, ssh_key=None):
    """Clone a repo and checkout the specified ref."""
    print(f"  Cloning {repo_url} ...")
    ok, out, err = run_git(["clone", repo_url, str(target_dir)], ssh_key=ssh_key)
    if not ok:
        print(f"  ERROR cloning: {err}")
        return False

    ok, out, err = run_git(["checkout", ref], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        print(f"  ERROR checking out ref '{ref}': {err}")
        return False

    print(f"  Checked out ref: {ref}")
    return True


def update_repo(name, repo_url, ref, target_dir, ssh_key=None):
    """Fetch and checkout the specified ref in an existing clone."""
    print(f"  Fetching updates ...")
    ok, out, err = run_git(["fetch", "--all", "--prune"], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        print(f"  ERROR fetching: {err}")
        return False

    ok, out, err = run_git(["checkout", ref], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        print(f"  ERROR checking out ref '{ref}': {err}")
        return False

    # If ref is a branch, pull latest
    ok_branch, _, _ = run_git(
        ["symbolic-ref", "--short", "HEAD"], cwd=target_dir
    )
    if ok_branch:
        run_git(["pull", "--ff-only"], cwd=target_dir, ssh_key=ssh_key)

    print(f"  Checked out ref: {ref}")
    return True


def main():
    if not MANIFEST.exists():
        print(f"No {MANIFEST.name} found — nothing to fetch.")
        sys.exit(0)

    with open(MANIFEST) as f:
        config = yaml.safe_load(f)

    sources = config.get("sources") or []
    if not sources:
        print("No sources defined in manifest.")
        sys.exit(0)

    REMOTE_DIR.mkdir(exist_ok=True)

    declared_names = set()
    errors = 0

    for source in sources:
        name = source["name"]
        repo_url = source["repo"]
        path = source.get("path", ".")
        ref = source.get("ref", "main")
        key = source.get("key")
        declared_names.add(name)

        # Resolve key path relative to project root
        ssh_key = None
        if key:
            ssh_key = str((PROJECT_ROOT / key).resolve())
            if not Path(ssh_key).is_file():
                print(f"\n[{name}]")
                print(f"  ERROR: SSH key not found: {key}")
                errors += 1
                continue

        print(f"\n[{name}]")
        target_dir = REMOTE_DIR / name

        if target_dir.exists():
            ok = update_repo(name, repo_url, ref, target_dir, ssh_key=ssh_key)
        else:
            ok = clone_repo(name, repo_url, ref, target_dir, ssh_key=ssh_key)

        if not ok:
            errors += 1
            continue

        # Validate that the specified path exists
        tools_path = target_dir / path
        if not tools_path.is_dir():
            print(f"  WARNING: path '{path}' not found in cloned repo")

    # Cleanup: remove directories not in the manifest
    if REMOTE_DIR.exists():
        for child in REMOTE_DIR.iterdir():
            if child.is_dir() and child.name not in declared_names:
                print(f"\nRemoving stale repo: {child.name}")
                shutil.rmtree(child)

    print(f"\nDone. {len(declared_names)} source(s) processed, {errors} error(s).")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
