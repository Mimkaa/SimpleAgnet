from agent.config import load_config
from agent.storage.task_store import TaskStore
from agent.storage.event_log import EventLog
from agent.storage.artifacts import Artifacts
from agent.agent_loop import AgentLoop
from agent.interfaces.cli_interface import CliInterface
from agent.workflows.firewall_project import FirewallProjectWorkflow


def main():
    cfg = load_config()

    task_store = TaskStore(cfg.TASKS_FILE)
    event_log = EventLog(cfg.EVENTS_FILE)
    artifacts = Artifacts(cfg.ARTIFACTS_DIR)

    agent = AgentLoop(
        task_store=task_store,
        event_log=event_log,
        workflows=[
            FirewallProjectWorkflow()
        ],
        artifacts=artifacts,
        target_project_dir=cfg.TARGET_PROJECT_DIR,
    )

    CliInterface(agent).run()


if __name__ == "__main__":
    main()