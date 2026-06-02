from pathlib import Path

from agent.tools.apply_safe_change_tool import apply_safe_change
from agent.tools.artifact_transform_tool import transform_artifacts
from agent.tools.git_clone_tool import run_git_clone
from agent.tools.materialize_artifact_tool import materialize_artifact
from agent.tools.self_improvement_pipeline_tool import execute_approved_self_improvement_pipeline
from agent.tools.set_target_project_tool import run_set_target_project
from agent.tools.source_snapshot_tool import create_source_snapshot
from agent.tools.subworkflow_tool import execute_subworkflow
from agent.tools.verify_target_file_tool import verify_target_file


def _agent_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_shell_cwd(agent_loop, action):
    cwd = action.get("cwd")

    if cwd in (None, "", "target_project"):
        return str(agent_loop.target_project_dir)

    if cwd == "agent_repo":
        return str(_agent_repo_root())

    return str(agent_loop.target_project_dir)


def run_shell_tool(agent_loop, task, action):
    return agent_loop.run_tool(
        "shell",
        command=action["command"],
        cwd=_resolve_shell_cwd(agent_loop, action),
    )


def run_file_tool(agent_loop, task, action):
    return agent_loop.run_tool(
        "file",
        action=action["action"],
        path=action["path"],
        content=action.get("content", ""),
    )


def run_artifact_transform_tool(agent_loop, task, action):
    return transform_artifacts(agent_loop, task, action)


def run_source_snapshot_tool(agent_loop, task, action):
    return create_source_snapshot(agent_loop, task, action)


def run_apply_safe_change_tool(agent_loop, task, action):
    return apply_safe_change(agent_loop, task, action)


def run_verify_target_file_tool(agent_loop, task, action):
    return verify_target_file(agent_loop, task, action)


def run_self_improvement_pipeline_tool(agent_loop, task, action):
    return execute_approved_self_improvement_pipeline(agent_loop, task, action)


def run_materialize_artifact_tool(agent_loop, task, action):
    return materialize_artifact(agent_loop, task, action)


def run_subworkflow_tool(agent_loop, task, action):
    return execute_subworkflow(agent_loop, task, action)


def run_git_clone_tool(agent_loop, task, action):
    return run_git_clone(agent_loop, task, action)


def run_set_target_project_tool(agent_loop, task, action):
    return run_set_target_project(agent_loop, task, action)


def run_list_project_files_tool(agent_loop, task, action):
    base = agent_loop.target_project_dir
    max_files = int(action.get("max_files", 100))
    max_files = max(1, min(max_files, 1000))
    include_dirs = bool(action.get("include_dirs", False))
    skip_parts = {".git", ".venv", "__pycache__", ".agent_data"}

    files = []
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        if any(part in skip_parts for part in rel.parts):
            continue
        if path.is_dir() and not include_dirs:
            continue
        files.append(rel.as_posix())
        if len(files) >= max_files:
            break

    return {
        "ok": True,
        "root": str(base),
        "count": len(files),
        "files": files,
    }


def run_read_project_file_tool(agent_loop, task, action):
    base = agent_loop.target_project_dir.resolve()
    raw_path = action.get("path") or action.get("file")

    if not raw_path:
        return {
            "ok": False,
            "message": "read_project_file requires a path.",
        }

    candidate = (base / str(raw_path)).resolve()

    try:
        relative = candidate.relative_to(base)
    except ValueError:
        return {
            "ok": False,
            "message": "Path is outside the target project.",
            "path": str(raw_path),
        }

    skip_parts = {".git", ".venv", "__pycache__", ".agent_data"}
    if any(part in skip_parts for part in relative.parts):
        return {
            "ok": False,
            "message": "Refusing to read internal or generated project folder.",
            "path": relative.as_posix(),
        }

    if not candidate.exists():
        return {
            "ok": False,
            "message": "File does not exist.",
            "path": relative.as_posix(),
        }

    if not candidate.is_file():
        return {
            "ok": False,
            "message": "Path is not a file.",
            "path": relative.as_posix(),
        }

    max_chars = int(action.get("max_chars", 20000))
    max_chars = max(1, min(max_chars, 200000))

    content = candidate.read_text(encoding=action.get("encoding", "utf-8"), errors="replace")
    truncated = len(content) > max_chars

    return {
        "ok": True,
        "path": relative.as_posix(),
        "chars": len(content),
        "truncated": truncated,
        "content": content[:max_chars],
    }


def run_search_project_files_tool(agent_loop, task, action):
    base = agent_loop.target_project_dir.resolve()
    query = action.get("query") or action.get("text") or action.get("pattern")

    if not query:
        return {
            "ok": False,
            "message": "search_project_files requires a query.",
        }

    query = str(query)
    case_sensitive = bool(action.get("case_sensitive", False))
    needle = query if case_sensitive else query.lower()

    max_files = int(action.get("max_files", 200))
    max_files = max(1, min(max_files, 1000))
    max_matches = int(action.get("max_matches", 100))
    max_matches = max(1, min(max_matches, 1000))

    skip_parts = {
        ".git",
        ".venv",
        "__pycache__",
        ".agent_data",
        "node_modules",
        "dist",
        "build",
    }

    scanned_files = 0
    matched_files = set()
    matches = []

    for candidate in base.rglob("*"):
        if len(matches) >= max_matches or scanned_files >= max_files:
            break

        try:
            relative = candidate.resolve().relative_to(base)
        except ValueError:
            continue

        if any(part in skip_parts for part in relative.parts):
            continue

        if not candidate.is_file():
            continue

        scanned_files += 1

        try:
            content = candidate.read_text(
                encoding=action.get("encoding", "utf-8"),
                errors="replace",
            )
        except OSError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            haystack = line if case_sensitive else line.lower()
            if needle in haystack:
                matched_files.add(relative.as_posix())
                matches.append(
                    {
                        "path": relative.as_posix(),
                        "line": line_number,
                        "text": line[:500],
                    }
                )
                if len(matches) >= max_matches:
                    break

    return {
        "ok": True,
        "query": query,
        "scanned_files": scanned_files,
        "matched_file_count": len(matched_files),
        "count": len(matches),
        "matches": matches,
    }
