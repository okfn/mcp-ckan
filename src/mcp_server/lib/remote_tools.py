"""
Fetch remote tool repositories declared in tool_sources.yaml

Clones or updates git repos into remote_tools/<name>/ and checks out
the specified ref. Removes repos no longer present in the manifest.
"""

import logging
import shutil
import subprocess
from pathlib import Path

import yaml


log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = PROJECT_ROOT / "deploy/tool_sources.yaml"
REMOTE_DIR = PROJECT_ROOT / "remote_tools"


def _run_git(args, cwd=None, ssh_key=None):
    """Run a git command and return (success, stdout, stderr).

    If ssh_key is provided, sets GIT_SSH_COMMAND so git uses that
    specific private key for authentication.
    """
    import os
    env = None
    if ssh_key:
        env = {
            **os.environ,
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


def _clone_repo(name, repo_url, ref, target_dir, ssh_key=None):
    """Clone a repo and checkout the specified ref."""
    log.info(f"  Cloning {repo_url} ...")
    ok, out, err = _run_git(["clone", repo_url, str(target_dir)], ssh_key=ssh_key)
    if not ok:
        log.error(f"  ERROR cloning: {err}")
        return False

    ok, out, err = _run_git(["checkout", ref], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        log.error(f"  ERROR checking out ref '{ref}': {err}")
        return False

    log.info(f"  Checked out ref: {ref}")
    return True


def _update_repo(name, repo_url, ref, target_dir, ssh_key=None):
    """Fetch and checkout the specified ref in an existing clone."""
    log.info("  Fetching updates ...")
    ok, out, err = _run_git(["fetch", "--all", "--prune"], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        log.error(f"  ERROR fetching: {err}")
        return False

    ok, out, err = _run_git(["checkout", ref], cwd=target_dir, ssh_key=ssh_key)
    if not ok:
        log.error(f"  ERROR checking out ref '{ref}': {err}")
        return False

    # If ref is a branch, pull latest
    ok_branch, _, _ = _run_git(["symbolic-ref", "--short", "HEAD"], cwd=target_dir)
    if ok_branch:
        _run_git(["pull", "--ff-only"], cwd=target_dir, ssh_key=ssh_key)

    log.info(f"  Checked out ref: {ref}")
    return True


def fetch_remote_tools():
    """Fetch all remote tool repositories declared in tool_sources.yaml.

    Clones new repos and updates existing ones. Removes repos no longer
    present in the manifest.

    Returns:
        int: Number of errors encountered (0 means success).
    """
    if not MANIFEST.exists():
        log.warning(f"No {MANIFEST.name} found — nothing to fetch.")
        return 0

    with open(MANIFEST) as f:
        config = yaml.safe_load(f)

    sources = config.get("sources") or []
    if not sources:
        log.warning("No sources defined in manifest.")
        return 0

    REMOTE_DIR.mkdir(exist_ok=True)

    declared_names = set()
    errors = 0

    for source in sources:
        name = source["name"]
        repo_url = source["repo"]
        ref = source.get("ref", "main")
        key = source.get("key")
        declared_names.add(name)

        # Resolve key path relative to project root
        ssh_key = None
        if key:
            ssh_key = str((PROJECT_ROOT / key).resolve())
            if not Path(ssh_key).is_file():
                log.error(f"[{name}] SSH key not found: {key}")
                errors += 1
                continue

        log.info(f"[{name}]")
        target_dir = REMOTE_DIR / name

        if target_dir.exists():
            ok = _update_repo(name, repo_url, ref, target_dir, ssh_key=ssh_key)
        else:
            ok = _clone_repo(name, repo_url, ref, target_dir, ssh_key=ssh_key)

        if not ok:
            errors += 1
            continue

        # Validate that the specified path exists
        path = source.get("path", ".")
        tools_path = target_dir / path
        if not tools_path.is_dir():
            log.warning(f"  [{name}] path '{path}' not found in cloned repo")

    # Cleanup: remove directories not in the manifest
    if REMOTE_DIR.exists():
        for child in REMOTE_DIR.iterdir():
            if child.is_dir() and child.name not in declared_names:
                log.info(f"Removing stale repo: {child.name}")
                shutil.rmtree(child)

    log.info(f"Fetch complete. {len(declared_names)} source(s) processed, {errors} error(s).")
    return errors
