class CliInterface:
    def __init__(self, agent):
        self.agent = agent

    def run(self):
        print("Minimal Agent CLI")
        print(
            "Commands: help, goal <text>, tasks, next, exec, artifact <name>, "
            "done <id>, fail <id>, shell <cmd>, log, exit"
        )

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
                print("goal <text>       - create tasks from goal")
                print("tasks             - list tasks")
                print("next              - show next pending task + suggested action")
                print("exec              - execute next pending task")
                print("artifact <name>   - show artifact content")
                print("done <id>         - mark task done")
                print("fail <id>         - mark task failed")
                print("shell <cmd>       - run shell command")
                print("log               - show recent events")
                print("exit              - exit CLI")
                continue

            if line.startswith("goal "):
                goal = line[len("goal "):]
                tasks = self.agent.create_goal(goal)
                for t in tasks:
                    print(f"[{t.status}] {t.id} - {t.title}")
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
                cmd = line[len("shell "):]
                result = self.agent.run_tool("shell", command=cmd)
                print(result.get("stdout", ""))

                if result.get("stderr"):
                    print(result["stderr"])

                continue

            if line == "log":
                for event in self.agent.recent_events():
                    print(event)
                continue

            print("Unknown command. Type `help`.")