from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


GITHUB_HTTPS_RE = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def parse_github_repo_url(repo_url: str) -> tuple[str, str, str]:
    """
    Validate and normalize a public HTTPS GitHub repository URL.

    Returns:
        (normalized_url, owner, repo_name)

    Raises:
        ValueError if the URL is not an allowed GitHub HTTPS repo URL.
    """
    repo_url = (repo_url or "").strip()
    match = GITHUB_HTTPS_RE.match(repo_url)

    if not match:
        raise ValueError(
            "Only normal HTTPS GitHub repo URLs are allowed, for example: "
            "https://github.com/owner/repo"
        )

    owner, repo_name = match.groups()
    repo_name = repo_name.removesuffix(".git")

    parsed = urlparse(repo_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError("Only https://github.com/... URLs are allowed.")

    normalized_url = f"https://github.com/{owner}/{repo_name}.git"
    return normalized_url, owner, repo_name


def safe_relative_dir(raw_dir: str | None, default: str = "target_projects") -> Path:
    """
    Accept only safe relative directories inside the agent repo.
    """
    raw_dir = (raw_dir or default).strip() or default
    path = Path(raw_dir)

    if path.is_absolute():
        raise ValueError("Destination root must be a relative path.")

    if any(part in {"..", ""} for part in path.parts):
        raise ValueError("Destination root must not contain '..' or empty parts.")

    return path


def run_git_clone(agent_loop, task, action: dict) -> dict:
    """
    Safely clone a GitHub repository into a controlled folder inside the agent repo.

    Required action field:
        repo_url or url

    Optional action fields:
        destination_root: relative folder inside the agent repo, default target_projects
        depth: integer depth for shallow clone, default 1
    """
    try:
        repo_url = action.get("repo_url") or action.get("url")
        normalized_url, owner, repo_name = parse_github_repo_url(repo_url)

        repo_root = Path(__file__).resolve().parents[2]
        destination_root = safe_relative_dir(action.get("destination_root"))
        destination_base = (repo_root / destination_root).resolve()

        try:
            destination_base.relative_to(repo_root.resolve())
        except ValueError:
            return {
                "ok": False,
                "message": "Refusing to clone outside the agent repository.",
                "destination_base": str(destination_base),
            }

        destination = (destination_base / repo_name).resolve()

        try:
            destination.relative_to(destination_base)
        except ValueError:
            return {
                "ok": False,
                "message": "Refusing unsafe clone destination.",
                "destination": str(destination),
            }

        if destination.exists():
            return {
                "ok": False,
                "message": "Destination already exists; refusing to overwrite.",
                "repo_url": normalized_url,
                "destination": str(destination),
            }

        depth = int(action.get("depth", 1))
        depth = max(1, min(depth, 100))

        destination_base.mkdir(parents=True, exist_ok=True)

        git_version = subprocess.run(
            ["git", "--version"],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            timeout=30,
        )

        if git_version.returncode != 0:
            return {
                "ok": False,
                "message": "git is not available on PATH.",
                "stdout": git_version.stdout,
                "stderr": git_version.stderr,
            }

        clone_command = [
            "git",
            "clone",
            "--depth",
            str(depth),
            normalized_url,
            str(destination),
        ]

        completed = subprocess.run(
            clone_command,
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            timeout=int(action.get("timeout", 300)),
        )

        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "repo_url": normalized_url,
            "owner": owner,
            "repo_name": repo_name,
            "destination": str(destination),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "command": " ".join(clone_command),
        }

    except Exception as exc:
        return {
            "ok": False,
            "message": str(exc),
        }
