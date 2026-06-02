from __future__ import annotations

from pathlib import Path


def _agent_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _validate_simple_project_name(project_name: str) -> str:
    project_name = (project_name or "").strip()

    if not project_name:
        raise ValueError("Project name is required, for example: set target project PacketGuard")

    forbidden = {"", ".", ".."}
    if project_name in forbidden:
        raise ValueError("Invalid project name.")

    if "/" in project_name or "\\" in project_name:
        raise ValueError("Project name must be a single folder name, not a path.")

    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(ch not in allowed_chars for ch in project_name):
        raise ValueError("Project name contains unsupported characters.")

    return project_name


def run_set_target_project(agent_loop, task, action: dict) -> dict:
    """
    Set target_projects/<project_name> as the active target project.

    This writes .agent_data/target_project_override.txt in the agent repo.
    agent.config.load_config reads that file when it exists.
    """
    try:
        repo_root = _agent_repo_root()
        project_name = _validate_simple_project_name(action.get("project_name", ""))

        destination_root = action.get("destination_root", "target_projects")
        destination_root_path = Path(destination_root)

        if destination_root_path.is_absolute():
            return {
                "ok": False,
                "message": "destination_root must be relative.",
            }

        if any(part in {"", ".", ".."} for part in destination_root_path.parts):
            return {
                "ok": False,
                "message": "destination_root contains unsafe path parts.",
            }

        target = (repo_root / destination_root_path / project_name).resolve()

        try:
            target.relative_to(repo_root.resolve())
        except ValueError:
            return {
                "ok": False,
                "message": "Refusing to set target project outside the agent repo.",
                "target": str(target),
            }

        if not target.exists():
            return {
                "ok": False,
                "message": "Target project folder does not exist.",
                "project_name": project_name,
                "target": str(target),
            }

        if not target.is_dir():
            return {
                "ok": False,
                "message": "Target project is not a directory.",
                "project_name": project_name,
                "target": str(target),
            }

        marker_dir = repo_root / ".agent_data"
        marker_dir.mkdir(parents=True, exist_ok=True)

        marker = marker_dir / "target_project_override.txt"
        marker.write_text(str(target), encoding="utf-8")

        return {
            "ok": True,
            "project_name": project_name,
            "target_project_dir": str(target),
            "marker": str(marker),
            "message": "Active target project override written. Restart the CLI to see it in the startup banner.",
        }

    except Exception as exc:
        return {
            "ok": False,
            "message": str(exc),
        }
