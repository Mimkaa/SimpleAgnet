class CliInterface:
    def __init__(self, agent):
        self.agent = agent

    def print_known_artifacts(self):
        important_artifacts = [
            "project_profile.md",
            "entry_point.md",
            "core_components.md",
            "core_source_snapshot.md",
            "confirmed_runtime_flow.md",
            "test_results.txt",
            "test_behavior_report.md",
            "final_behavior_report.md",
            "runtime_flow_explanation.md",
        ]

        print("Known artifacts:")

        for artifact_name in important_artifacts:
            exists = self.agent.artifacts.exists(artifact_name)
            status = "yes" if exists else "no"
            print(f"- {artifact_name}: {status}")

    def auto_exec(self, max_steps: int = 25):
        steps = 0

        while steps < max_steps:
            task = self.agent.next_task()

            if not task:
                print(f"auto-exec stopped: no pending tasks after {steps} step(s).")
                return {
                    "ok": True,
                    "reason": "No pending tasks.",
                    "steps": steps,
                }

            print(f"auto-exec step {steps + 1}: {task.id} - {task.title}")

            result = self.agent.execute_next_action()
            print(result)

            steps += 1

            verification = result.get("verification", {}) if isinstance(result, dict) else {}
            verification_status = verification.get("status")

            if not isinstance(result, dict):
                print("auto-exec stopped: result was not a dictionary.")
                return {
                    "ok": False,
                    "reason": "Result was not a dictionary.",
                    "steps": steps,
                    "last_result": result,
                }

            if result.get("ok") is False:
                print("auto-exec stopped: result ok=False.")
                return {
                    "ok": False,
                    "reason": "Result ok=False.",
                    "steps": steps,
                    "last_result": result,
                }

            if verification_status and verification_status != "PASS":
                print(f"auto-exec stopped: verification status={verification_status}.")
                return {
                    "ok": False,
                    "reason": f"Verification status={verification_status}.",
                    "steps": steps,
                    "last_result": result,
                }

        print(f"auto-exec stopped: reached max_steps={max_steps}.")
        return {
            "ok": False,
            "reason": f"Reached max_steps={max_steps}.",
            "steps": steps,
        }

    def run(self):
        print("Minimal Agent CLI")
        print(
            "Commands: help, goal <text>, tasks, next, exec, auto-exec [max_steps], clear-pending, artifact <name>, "
            "artifact-exists <name>, artifacts, done <id>, fail <id>, "
            "shell <cmd>, log, exit"
        )
        print(f"Target project: {self.agent.target_project_dir}")
        self.print_known_artifacts()

        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            if line == "exit":
                break

            if line == "help":
                print("clear-pending          - remove all pending tasks")
                print("goal <text>            - create tasks from goal")
                print("tasks                  - list tasks")
                print("next                   - show next pending task + suggested action")
                print("exec                   - execute next pending task")
                print("auto-exec [max_steps]  - execute pending tasks until ok=False, verification failure, no pending tasks, or max_steps")
                print("artifact <name>        - show artifact content")
                print("artifact-exists <name> - check whether an artifact exists")
                print("artifacts              - show known important artifacts")
                print("done <id>              - mark task done")
                print("fail <id>              - mark task failed")
                print("shell <cmd>            - run shell command in target project")
                print("log                    - show recent events")
                print("exit                   - exit CLI")
                continue

            if line.startswith("goal "):
                goal = line[len("goal "):]
                tasks = self.agent.create_goal(goal)
                for t in tasks:
                    print(f"[{t.status}] {t.id} - {t.title}")
                continue

            if line == "clear-pending":
                removed = self.agent.clear_pending_tasks()
                print(f"Cleared {removed} pending task(s).")
                continue

            if line == "tasks":
                for t in self.agent.list_tasks():
                    print(f"[{t.status}] {t.id} - {t.title}")
                continue

            if line == "next":
                task = self.agent.next_task()
                if not task:
                    print("No pending tasks.")
                    continue

                print(f"Next: {task.id} - {task.title}")
                print(task.description)
                print("Suggested:", self.agent.suggest_next_action())
                continue

            if line == "exec":
                result = self.agent.execute_next_action()
                print(result)
                continue

            if line == "auto-exec" or line.startswith("auto-exec "):
                parts = line.split(maxsplit=1)
                max_steps = 25

                if len(parts) == 2:
                    try:
                        max_steps = int(parts[1])
                    except ValueError:
                        print("Usage: auto-exec [max_steps]")
                        continue

                if max_steps < 1:
                    print("max_steps must be at least 1.")
                    continue

                self.auto_exec(max_steps=max_steps)
                continue

            if line == "artifacts":
                self.print_known_artifacts()
                continue

            if line.startswith("artifact-exists "):
                artifact_name = line[len("artifact-exists "):].strip()

                if not artifact_name:
                    print("Usage: artifact-exists <artifact_name>")
                    continue

                print(self.agent.artifacts.exists(artifact_name))
                continue

            if line.startswith("artifact "):
                artifact_name = line[len("artifact "):].strip()

                if not artifact_name:
                    print("Usage: artifact <artifact_name>")
                    continue

                try:
                    content = self.agent.read_artifact(artifact_name)

                    print()
                    print(f"--- {artifact_name} ---")
                    print(content)
                    print(f"--- end of {artifact_name} ---")
                    print()

                except Exception as e:
                    print(f"Could not read artifact: {e}")

                continue

            if line.startswith("done "):
                task_id = line[len("done "):].strip()
                self.agent.mark_done(task_id)
                print("Marked done.")
                continue

            if line.startswith("fail "):
                task_id = line[len("fail "):].strip()
                self.agent.mark_failed(task_id)
                print("Marked failed.")
                continue

            if line.startswith("shell "):
                cmd = line[len("shell "):].strip()

                if not cmd:
                    print("Usage: shell <command>")
                    continue

                result = self.agent.run_tool(
                    "shell",
                    command=cmd,
                    cwd=str(self.agent.target_project_dir),
                )

                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")

                if stdout:
                    print(stdout, end="" if stdout.endswith("\n") else "\n")

                if stderr:
                    print(stderr, end="" if stderr.endswith("\n") else "\n")

                if not stdout and not stderr:
                    print(result)

                continue

            if line == "log":
                for event in self.agent.recent_events():
                    print(event)
                continue

            print("Unknown command. Type `help`.")
