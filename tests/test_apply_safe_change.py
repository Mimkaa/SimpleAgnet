# tests/test_apply_safe_change.py

from pathlib import Path
from agent.agent_loop import AgentLoop
from agent.state.task_state import Task


class DummyArtifacts:
    def write_text(self, name, content):
        self.last_name = name
        self.last_content = content
        return Path(name)


class DummyEventLog:
    def write(self, event, data):
        pass


class DummyTool:
    pass


def make_agent(tmp_path):
    return AgentLoop(
        task_store=None,
        event_log=DummyEventLog(),
        workflows=[],
        artifacts=DummyArtifacts(),
        target_project_dir=tmp_path,
    )


def test_apply_safe_change_normal_path(tmp_path):
    agent = make_agent(tmp_path)

    task = Task(
        title="test",
        description="test",
        inputs=[],
        outputs=["report.md"],
        tool_hint="apply_safe_change",
        kind="normal",
    )

    result = agent.apply_safe_change(task, {
        "target_file": "tmp_test.txt",
        "outputs": ["report.md"],
        "old_text": "OLD_VALUE",
        "new_text": "NEW_VALUE",
        "expected_text": "NEW_VALUE",
        "forbidden_text": "OLD_VALUE",
        "setup_text": "OLD_VALUE",
        "cleanup_after": True,
        "run_command": "python -c \"print('ok')\"",
    })

    assert result["ok"] is True
    assert result["expected_failure_observed"] is False
    assert not (tmp_path / "tmp_test.txt").exists()
    assert not (tmp_path / "tmp_test.txt.bak").exists()


def test_apply_safe_change_expected_rollback_path(tmp_path):
    agent = make_agent(tmp_path)

    task = Task(
        title="test rollback",
        description="test rollback",
        inputs=[],
        outputs=["rollback_report.md"],
        tool_hint="apply_safe_change",
        kind="normal",
    )

    result = agent.apply_safe_change(task, {
        "target_file": "tmp_rollback_test.txt",
        "outputs": ["rollback_report.md"],
        "old_text": "OLD_VALUE",
        "new_text": "NEW_VALUE",
        "expected_text": "IMPOSSIBLE_EXPECTED_TEXT",
        "forbidden_text": "OLD_VALUE",
        "setup_text": "OLD_VALUE",
        "cleanup_after": True,
        "run_command": "python -c \"print('ok')\"",
        "expected_failure": True,
    })

    assert result["ok"] is False
    assert result["expected_failure_observed"] is True
    assert result["rollback_done"] is True
    assert not (tmp_path / "tmp_rollback_test.txt").exists()
    assert not (tmp_path / "tmp_rollback_test.txt.bak").exists()