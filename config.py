from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    DATA_DIR: Path
    TASKS_FILE: Path
    EVENTS_FILE: Path
    ARTIFACTS_DIR: Path
    TARGET_PROJECT_DIR: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _target_project_dir(repo_root: Path) -> Path:
    override_file = repo_root / ".agent_data" / "target_project_override.txt"

    if override_file.exists():
        raw = override_file.read_text(encoding="utf-8").strip()

        if raw:
            candidate = Path(raw)

            if not candidate.is_absolute():
                candidate = repo_root / candidate

            candidate = candidate.resolve()

            try:
                candidate.relative_to(repo_root.resolve())
            except ValueError:
                raise ValueError(
                    "Refusing TARGET_PROJECT_DIR override outside the agent repository: "
                    f"{candidate}"
                )

            if candidate.exists() and candidate.is_dir():
                return candidate

    return Path(r"C:\Users\illa9\Downloads\job_application_project")


def load_config() -> Config:
    repo_root = _repo_root()
    data_dir = repo_root / ".agent_data"

    return Config(
        DATA_DIR=data_dir,
        TASKS_FILE=data_dir / "tasks.json",
        EVENTS_FILE=data_dir / "events.jsonl",
        ARTIFACTS_DIR=data_dir / "artifacts",
        TARGET_PROJECT_DIR=_target_project_dir(repo_root),
    )
