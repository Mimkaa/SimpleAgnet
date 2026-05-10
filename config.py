from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class Config:
    BASE_DIR: Path = Path(os.environ.get("AGENT_BASE_DIR", ".")).resolve()
    DATA_DIR: Path = Path(os.environ.get("AGENT_DATA_DIR", ".agent_data")).resolve()

    TARGET_PROJECT_DIR: Path = Path(
        os.environ.get(
            "TARGET_PROJECT_DIR",
            r"C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project",
        )
    ).resolve()

    TASKS_FILE: Path = DATA_DIR / "tasks.json"
    EVENTS_FILE: Path = DATA_DIR / "events.jsonl"
    ARTIFACTS_DIR: Path = DATA_DIR / "artifacts"


def load_config() -> Config:
    cfg = Config()
    cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if not cfg.TASKS_FILE.exists():
        cfg.TASKS_FILE.write_text("[]", encoding="utf-8")

    if not cfg.EVENTS_FILE.exists():
        cfg.EVENTS_FILE.write_text("", encoding="utf-8")

    return cfg