from agent.state.task_state import Task


class AgentUpdateInstructionsWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "apply agent update instructions" in lower_goal
            or "apply update instructions" in lower_goal
            or "process agent update instructions" in lower_goal
            or "apply gpt update instructions" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Verify agent update instructions",
                description=(
                    "Verify that agent_update_instructions.md exists in the agent repo root."
                ),
                inputs=[],
                outputs=["agent_update_instruction_check.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import os; "
                        "repo=Path(os.environ.get('AGENT_REPO_ROOT', r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo')); "
                        "p=repo / 'agent_update_instructions.md'; "
                        "print('repo=', repo); "
                        "print('instructions=', p); "
                        "print('exists=', p.exists()); "
                        "print('chars=', len(p.read_text(encoding='utf-8')) if p.exists() else 0); "
                        "raise SystemExit(0 if p.exists() and p.read_text(encoding='utf-8').strip() else 1)"
                        "\""
                    ),
                    "outputs": ["agent_update_instruction_check.md"],
                    "reason": (
                        "Confirm that the browser GPT update instructions file exists before applying changes."
                    ),
                },
            ),

            Task(
                title="Apply exact file writes from update instructions",
                description=(
                    "Parse agent_update_instructions.md and write exact code blocks to declared files."
                ),
                inputs=["agent_update_instruction_check.md"],
                outputs=["agent_update_file_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import base64; "
                        "script=Path('.agent_data/apply_agent_update_instructions.py'); "
                        "script.parent.mkdir(parents=True, exist_ok=True); "
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBvcwppbXBvcnQgcmUKCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCByIkM6XFVzZXJzXGlsbGE5XERvd25sb2Fkc1xtaW5pbWFsX2FnZW50X3JlcG9cbWluaW1hbF9hZ2VudF9yZXBvIikpLnJlc29sdmUoKQppbnN0cnVjdGlvbnMgPSByZXBvIC8gImFnZW50X3VwZGF0ZV9pbnN0cnVjdGlvbnMubWQiCnRleHQgPSBpbnN0cnVjdGlvbnMucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCgojIE1hdGNoIHNlY3Rpb25zIGxpa2U6CiMgIyMjIGFnZW50L3Rvb2xzL2ZpbGUucHkKIyBgYGBweXRob24KIyAuLi4KIyBgYGAKIyBBbHNvIGFjY2VwdHMgZmVuY2VzIHdpdGggYXR0cmlidXRlcywgZS5nLiBgYGBweXRob24gaWQ9ImFiYyIKcGF0dGVybiA9IHJlLmNvbXBpbGUoCiAgICByIl4jIyNccysoW15cbl0rPylccypcbmBgYFteXG5dKlxuKC4qPylcbmBgYCIsCiAgICByZS5NIHwgcmUuUywKKQoKbWF0Y2hlcyA9IHBhdHRlcm4uZmluZGFsbCh0ZXh0KQoKaWYgbm90IG1hdGNoZXM6CiAgICBwcmludCgicmVwbz0iLCByZXBvKQogICAgcHJpbnQoImluc3RydWN0aW9ucz0iLCBpbnN0cnVjdGlvbnMpCiAgICBwcmludCgiY2hhcnM9IiwgbGVuKHRleHQpKQogICAgcHJpbnQoImZpcnN0XzUwMF9jaGFycz0iKQogICAgcHJpbnQodGV4dFs6NTAwXSkKICAgIHJhaXNlIFN5c3RlbUV4aXQoIk5vIGZpbGUgd3JpdGUgYmxvY2tzIGZvdW5kLiBFeHBlY3RlZDogIyMjIHBhdGgvdG8vZmlsZS5weSBmb2xsb3dlZCBieSBmZW5jZWQgY29kZSBibG9jay4iKQoKd3JpdHRlbiA9IFtdCgpmb3IgcmF3X3BhdGgsIGNvbnRlbnQgaW4gbWF0Y2hlczoKICAgIHJlbCA9IHJhd19wYXRoLnN0cmlwKCkucmVwbGFjZSgiXFwiLCAiLyIpCiAgICBhc3NlcnQgbm90IHJlbC5zdGFydHN3aXRoKCIvIiksIGYiQWJzb2x1dGUgcGF0aHMgYXJlIG5vdCBhbGxvd2VkOiB7cmVsfSIKICAgIGFzc2VydCAiLi4iIG5vdCBpbiBQYXRoKHJlbCkucGFydHMsIGYiUGFyZW50IGRpcmVjdG9yeSB0cmF2ZXJzYWwgaXMgbm90IGFsbG93ZWQ6IHtyZWx9IgoKICAgIHRhcmdldCA9IChyZXBvIC8gcmVsKS5yZXNvbHZlKCkKICAgIGFzc2VydCBzdHIodGFyZ2V0KS5zdGFydHN3aXRoKHN0cihyZXBvKSksIGYiVGFyZ2V0IGVzY2FwZXMgcmVwbzoge3RhcmdldH0iCiAgICBhc3NlcnQgIi5lbnYiIG5vdCBpbiB0YXJnZXQubmFtZS5sb3dlcigpLCBmIlJlZnVzaW5nIHRvIGVkaXQgZW52L3NlY3JldHMgZmlsZToge3RhcmdldH0iCgogICAgdGFyZ2V0LnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICB0YXJnZXQud3JpdGVfdGV4dChjb250ZW50LnJzdHJpcCgpICsgIlxuIiwgZW5jb2Rpbmc9InV0Zi04IikKICAgIHdyaXR0ZW4uYXBwZW5kKHRhcmdldCkKCnByaW50KCJyZXBvPSIsIHJlcG8pCnByaW50KCJ3cml0dGVuX2NvdW50PSIsIGxlbih3cml0dGVuKSkKZm9yIHBhdGggaW4gd3JpdHRlbjoKICAgIHByaW50KCJ3cml0dGVuPSIsIHBhdGgpCgpyYWlzZSBTeXN0ZW1FeGl0KDAgaWYgd3JpdHRlbiBlbHNlIDEpCg=='; "
                        "script.write_text(base64.b64decode(code_b64).decode('utf-8'), encoding='utf-8'); "
                        "print('script=', script)"
                        "\" "
                        "&& python .agent_data/apply_agent_update_instructions.py"
                    ),
                    "outputs": ["agent_update_file_write_result.md"],
                    "reason": (
                        "Apply exact file writes from the instructions using a generated Python script. "
                        "Only relative paths inside the repo are allowed. No commits or pushes."
                    ),
                },
            ),

            Task(
                title="Run agent update checks",
                description=(
                    "Run checks listed under the Checks section of agent_update_instructions.md."
                ),
                inputs=["agent_update_file_write_result.md"],
                outputs=["agent_update_check_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import base64; "
                        "script=Path('.agent_data/run_agent_update_checks.py'); "
                        "script.parent.mkdir(parents=True, exist_ok=True); "
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBvcwppbXBvcnQgcmUKaW1wb3J0IHN1YnByb2Nlc3MKCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCByIkM6XFVzZXJzXGlsbGE5XERvd25sb2Fkc1xtaW5pbWFsX2FnZW50X3JlcG9cbWluaW1hbF9hZ2VudF9yZXBvIikpLnJlc29sdmUoKQppbnN0cnVjdGlvbnMgPSByZXBvIC8gImFnZW50X3VwZGF0ZV9pbnN0cnVjdGlvbnMubWQiCnRleHQgPSBpbnN0cnVjdGlvbnMucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCgptYXRjaCA9IHJlLnNlYXJjaChyIiMjXHMrQ2hlY2tzXHMqKC4qPykoPz1cbiMjXHMrfFxaKSIsIHRleHQsIHJlLlMgfCByZS5JKQpjaGVja3MgPSBbXQppZiBtYXRjaDoKICAgIGNoZWNrcyA9IFsKICAgICAgICBsaW5lLnN0cmlwKClbMjpdLnN0cmlwKCkKICAgICAgICBmb3IgbGluZSBpbiBtYXRjaC5ncm91cCgxKS5zcGxpdGxpbmVzKCkKICAgICAgICBpZiBsaW5lLnN0cmlwKCkuc3RhcnRzd2l0aCgiLSAiKQogICAgXQoKaWYgbm90IGNoZWNrczoKICAgIGNoZWNrcyA9IFsicHl0aG9uIC1tIHB5X2NvbXBpbGUgYWdlbnQvYWdlbnRfbG9vcC5weSJdCgpwcmludCgicmVwbz0iLCByZXBvKQpwcmludCgiY2hlY2tfY291bnQ9IiwgbGVuKGNoZWNrcykpCgpmYWlsZWQgPSBbXQoKZm9yIGNtZCBpbiBjaGVja3M6CiAgICBwcmludCgiUlVOPSIsIGNtZCkKICAgIHJlc3VsdCA9IHN1YnByb2Nlc3MucnVuKAogICAgICAgIGNtZCwKICAgICAgICBjd2Q9c3RyKHJlcG8pLAogICAgICAgIHNoZWxsPVRydWUsCiAgICAgICAgdGV4dD1UcnVlLAogICAgICAgIGNhcHR1cmVfb3V0cHV0PVRydWUsCiAgICApCiAgICBwcmludCgiUkVUVVJOX0NPREU9IiwgcmVzdWx0LnJldHVybmNvZGUpCiAgICBpZiByZXN1bHQuc3Rkb3V0OgogICAgICAgIHByaW50KCJTVERPVVQ9IiwgcmVzdWx0LnN0ZG91dCkKICAgIGlmIHJlc3VsdC5zdGRlcnI6CiAgICAgICAgcHJpbnQoIlNUREVSUj0iLCByZXN1bHQuc3RkZXJyKQogICAgaWYgcmVzdWx0LnJldHVybmNvZGUgIT0gMDoKICAgICAgICBmYWlsZWQuYXBwZW5kKChjbWQsIHJlc3VsdC5yZXR1cm5jb2RlKSkKCnByaW50KCJmYWlsZWQ9IiwgZmFpbGVkKQpyYWlzZSBTeXN0ZW1FeGl0KDAgaWYgbm90IGZhaWxlZCBlbHNlIDEpCg=='; "
                        "script.write_text(base64.b64decode(code_b64).decode('utf-8'), encoding='utf-8'); "
                        "print('script=', script)"
                        "\" "
                        "&& python .agent_data/run_agent_update_checks.py"
                    ),
                    "outputs": ["agent_update_check_result.md"],
                    "reason": (
                        "Run the exact checks requested in the update instructions. "
                        "If no checks are listed, run a minimal agent_loop.py py_compile check."
                    ),
                },
            ),

            Task(
                title="Write agent update result",
                description=(
                    "Write a final local update result report into the agent repo root."
                ),
                inputs=["agent_update_check_result.md"],
                outputs=["agent_update_result_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import base64; "
                        "script=Path('.agent_data/write_agent_update_result.py'); "
                        "script.parent.mkdir(parents=True, exist_ok=True); "
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmZyb20gZGF0ZXRpbWUgaW1wb3J0IGRhdGV0aW1lCmltcG9ydCBvcwppbXBvcnQgcmUKCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCByIkM6XFVzZXJzXGlsbGE5XERvd25sb2Fkc1xtaW5pbWFsX2FnZW50X3JlcG9cbWluaW1hbF9hZ2VudF9yZXBvIikpLnJlc29sdmUoKQppbnN0cnVjdGlvbnMgPSByZXBvIC8gImFnZW50X3VwZGF0ZV9pbnN0cnVjdGlvbnMubWQiCnJlc3VsdCA9IHJlcG8gLyAiYWdlbnRfdXBkYXRlX3Jlc3VsdC5tZCIKdGV4dCA9IGluc3RydWN0aW9ucy5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKCmZpbGVzID0gcmUuZmluZGFsbChyIl4jIyNccysoW15cbl0rKSIsIHRleHQsIHJlLk0pCgptYXRjaCA9IHJlLnNlYXJjaChyIiMjXHMrQ2hlY2tzXHMqKC4qPykoPz1cbiMjXHMrfFxaKSIsIHRleHQsIHJlLlMgfCByZS5JKQpjaGVja3MgPSAoCiAgICBbCiAgICAgICAgbGluZS5zdHJpcCgpWzI6XS5zdHJpcCgpCiAgICAgICAgZm9yIGxpbmUgaW4gbWF0Y2guZ3JvdXAoMSkuc3BsaXRsaW5lcygpCiAgICAgICAgaWYgbGluZS5zdHJpcCgpLnN0YXJ0c3dpdGgoIi0gIikKICAgIF0KICAgIGlmIG1hdGNoCiAgICBlbHNlIFsicHl0aG9uIC1tIHB5X2NvbXBpbGUgYWdlbnQvYWdlbnRfbG9vcC5weSJdCikKCnJlcG9ydCA9ICIjIEFnZW50IFVwZGF0ZSBSZXN1bHRcblxuIgpyZXBvcnQgKz0gIiMjIFN0YXR1c1xuUEFTU1xuXG4iCnJlcG9ydCArPSAiIyMgRmlsZXMgV3JpdHRlblxuIgpyZXBvcnQgKz0gIiIuam9pbigiLSAiICsgZmlsZSArICJcbiIgZm9yIGZpbGUgaW4gZmlsZXMpIGlmIGZpbGVzIGVsc2UgIi0gTm9uZVxuIgpyZXBvcnQgKz0gIlxuIgpyZXBvcnQgKz0gIiMjIENoZWNrcyBSdW5cbiIKcmVwb3J0ICs9ICIiLmpvaW4oIi0gIiArIGNoZWNrICsgIlxuIiBmb3IgY2hlY2sgaW4gY2hlY2tzKQpyZXBvcnQgKz0gIlxuIgpyZXBvcnQgKz0gIiMjIFRpbWVzdGFtcFxuIiArIGRhdGV0aW1lLm5vdygpLmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpICsgIlxuXG4iCnJlcG9ydCArPSAiIyMgTmV4dFxuUkVBRFlfRk9SX05FWFRfUFJPTVBUXG4iCgpyZXN1bHQud3JpdGVfdGV4dChyZXBvcnQsIGVuY29kaW5nPSJ1dGYtOCIpCgpwcmludCgicmVzdWx0PSIsIHJlc3VsdCkKcHJpbnQoIlJFQURZX0ZPUl9ORVhUX1BST01QVCIpCnJhaXNlIFN5c3RlbUV4aXQoMCBpZiByZXN1bHQuZXhpc3RzKCkgZWxzZSAxKQo='; "
                        "script.write_text(base64.b64decode(code_b64).decode('utf-8'), encoding='utf-8'); "
                        "print('script=', script)"
                        "\" "
                        "&& python .agent_data/write_agent_update_result.py"
                    ),
                    "outputs": ["agent_update_result_write_result.md"],
                    "reason": (
                        "Write agent_update_result.md so the result can be pasted back to browser GPT."
                    ),
                },
            ),
        ]