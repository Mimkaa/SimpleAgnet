from agent.state.task_state import Task


class FirewallProjectWorkflow:
    keywords = ["firewall", "packet", "iptables", "nftables", "network"]

    def can_handle(self, goal: str) -> bool:
        g = goal.lower()
        return any(k in g for k in self.keywords)

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Verify shell command execution",
                description="Run python --version to confirm shell execution and verifier logic work.",
                outputs=[
                    "shell_verification_test.json",
                ],
                tool_hint="shell",
                kind="test",
                action={
                    "tool": "shell",
                    "command": "py -3 --version",
                    "reason": "Verify that shell execution and verifier logic work.",
                },
            ),

            Task(
                title="Inspect project structure",
                description="List all files in the target project.",
                outputs=[
                    "project_structure_raw.txt",
                    "project_structure_summary.md",
                ],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": "dir /s /b",
                    "reason": "List all files in the target project.",
                },
            ),

            Task(
                title="Find the main entry point",
                description="Use the project structure summary to identify the likely entry point.",
                inputs=[
                    "project_structure_summary.md",
                ],
                outputs=[
                    "entry_point.md",
                ],
                tool_hint="analyze_artifact",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "project_structure_summary.md",
                    ],
                    "outputs": [
                        "entry_point.md",
                    ],
                    "reason": "Analyze project structure summary to identify the likely entry point.",
                },
            ),

            Task(
                title="Map the core components",
                description="Use the project structure summary to identify core components.",
                inputs=[
                    "project_structure_summary.md",
                ],
                outputs=[
                    "core_components.md",
                ],
                tool_hint="analyze_artifact",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "project_structure_summary.md",
                    ],
                    "outputs": [
                        "core_components.md",
                    ],
                    "reason": "Analyze project structure summary to map core components.",
                },
            ),

            Task(
                title="Read core source files",
                description="Read the actual source files needed to confirm runtime behavior.",
                inputs=[
                    "core_components.md",
                    "entry_point.md",
                ],
                outputs=[
                    "core_source_snapshot.md",
                ],
                tool_hint="read_source_files",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "files": [
                        "src/main.py",
                        "src/firewall.py",
                        "src/rule_engine.py",
                        "src/packet.py",
                        "src/decision.py",
                        "src/logger.py",
                        "rules/rules.json",
                        "README.md",
                    ],
                    "outputs": [
                        "core_source_snapshot.md",
                    ],
                    "reason": "Read important source files to confirm actual runtime behavior.",
                },
            ),

            Task(
                title="Confirm runtime flow from source",
                description="Use the source snapshot to confirm how the agent really runs.",
                inputs=[
                    "core_source_snapshot.md",
                ],
                outputs=[
                    "confirmed_runtime_flow.md",
                ],
                tool_hint="analyze_artifact",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "core_source_snapshot.md",
                    ],
                    "outputs": [
                        "confirmed_runtime_flow.md",
                    ],
                    "reason": "Analyze source snapshot to confirm actual runtime flow.",
                },
            ),

            Task(
                title="Trace one packet/request through the system",
                description="Use the confirmed runtime flow and component map to trace how a request moves through the system.",
                inputs=[
                    "confirmed_runtime_flow.md",
                    "core_components.md",
                ],
                outputs=[
                    "packet_flow.md",
                ],
                tool_hint="analyze_artifact",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "confirmed_runtime_flow.md",
                        "core_components.md",
                    ],
                    "outputs": [
                        "packet_flow.md",
                    ],
                    "reason": "Trace one packet/request through the system using confirmed flow and component map.",
                },
            ),

            Task(
                title="Make one tiny safe change",
                description="Suggest one tiny safe code/logging change based on the confirmed runtime flow and packet/request trace.",
                inputs=[
                    "confirmed_runtime_flow.md",
                    "packet_flow.md",
                ],
                outputs=[
                    "safe_change_suggestion.md",
                ],
                tool_hint="analyze_artifact",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "confirmed_runtime_flow.md",
                        "packet_flow.md",
                    ],
                    "outputs": [
                        "safe_change_suggestion.md",
                    ],
                    "reason": "Suggest one tiny safe code/logging change based on confirmed flow and packet/request trace.",
                },
            ),

            Task(
                title="Apply safe logger timestamp change",
                description="Update src/logger.py so UTC timestamps in the log end with Z.",
                inputs=[
                    "safe_change_suggestion.md",
                ],
                outputs=[
                    "change_report.md",
                ],
                tool_hint="apply_safe_change",
                kind="normal",
                action={
                    "tool": "apply_safe_change",
                    "target_file": "src/logger.py",
                    "outputs": [
                        "change_report.md",
                    ],
                    "reason": "Apply the approved tiny safe logger timestamp change.",
                },
            ),
        ]