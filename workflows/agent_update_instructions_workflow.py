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
                title="Apply file writes and replacements from update instructions",
                description=(
                    "Parse agent_update_instructions.md and apply exact file writes and exact block replacements."
                ),
                inputs=["agent_update_instruction_check.md"],
                outputs=["agent_update_file_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python C:/Users/illa9/Downloads/minimal_agent_repo/minimal_agent_repo/.agent_data/apply_agent_update_instructions.py"
                    ),
                    "outputs": ["agent_update_file_write_result.md"],
                    "reason": (
                        "Apply exact whole-file writes and exact block replacements from the instructions. "
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
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBvcwppbXBvcnQgcmUKaW1wb3J0IHN1YnByb2Nlc3MKCkRFRkFVTFRfUkVQTyA9IHIiQzpcVXNlcnNcaWxsYTlcRG93bmxvYWRzXG1pbmltYWxfYWdlbnRfcmVwb1xtaW5pbWFsX2FnZW50X3JlcG8iCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCBERUZBVUxUX1JFUE8pKS5yZXNvbHZlKCkKaW5zdHJ1Y3Rpb25zID0gcmVwbyAvICJhZ2VudF91cGRhdGVfaW5zdHJ1Y3Rpb25zLm1kIgp0ZXh0ID0gaW5zdHJ1Y3Rpb25zLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQoKZGVmIG1hcmtkb3duX3NlY3Rpb24obmFtZTogc3RyKSAtPiBzdHI6CiAgICBtYXRjaCA9IHJlLnNlYXJjaChyZiJeIyNccyt7cmUuZXNjYXBlKG5hbWUpfVxzKiguKj8pKD89XiMjXHMrfFxaKSIsIHRleHQsIHJlLk0gfCByZS5TIHwgcmUuSSkKICAgIHJldHVybiBtYXRjaC5ncm91cCgxKSBpZiBtYXRjaCBlbHNlICIiCgpkZWYgcmVuZGVyZWRfc2VjdGlvbihuYW1lOiBzdHIpIC0+IHN0cjoKICAgIGxpbmVzID0gdGV4dC5zcGxpdGxpbmVzKCkKICAgIHN0YXJ0ID0gTm9uZQogICAgZm9yIGksIGxpbmUgaW4gZW51bWVyYXRlKGxpbmVzKToKICAgICAgICBpZiBsaW5lLnN0cmlwKCkubG93ZXIoKSA9PSBuYW1lLmxvd2VyKCk6CiAgICAgICAgICAgIHN0YXJ0ID0gaSArIDEKICAgICAgICAgICAgYnJlYWsKICAgIGlmIHN0YXJ0IGlzIE5vbmU6CiAgICAgICAgcmV0dXJuICIiCiAgICBlbmQgPSBsZW4obGluZXMpCiAgICBzZWN0aW9uX25hbWVzID0geyJmaWxlcyB0byB3cml0ZSIsICJyZXBsYWNlbWVudHMiLCAiY2hlY2tzIn0KICAgIGZvciBqIGluIHJhbmdlKHN0YXJ0LCBsZW4obGluZXMpKToKICAgICAgICBpZiBsaW5lc1tqXS5zdHJpcCgpLmxvd2VyKCkgaW4gc2VjdGlvbl9uYW1lczoKICAgICAgICAgICAgZW5kID0gagogICAgICAgICAgICBicmVhawogICAgcmV0dXJuICJcbiIuam9pbihsaW5lc1tzdGFydDplbmRdKQoKY2hlY2tzX3NlY3Rpb24gPSBtYXJrZG93bl9zZWN0aW9uKCJDaGVja3MiKSBvciByZW5kZXJlZF9zZWN0aW9uKCJDaGVja3MiKQpjaGVja3MgPSBbXQpmb3IgbGluZSBpbiBjaGVja3Nfc2VjdGlvbi5zcGxpdGxpbmVzKCk6CiAgICBzdHJpcHBlZCA9IGxpbmUuc3RyaXAoKQogICAgaWYgbm90IHN0cmlwcGVkIG9yIHN0cmlwcGVkLnN0YXJ0c3dpdGgoImBgYCIpOgogICAgICAgIGNvbnRpbnVlCiAgICBpZiBzdHJpcHBlZCBpbiB7IlB5dGhvbiIsICJSdW4iLCAiVGV4dCIsICJKYXZhU2NyaXB0IiwgIkpTT04iLCAiTWFya2Rvd24ifToKICAgICAgICBjb250aW51ZQogICAgaWYgc3RyaXBwZWQgaW4geyJQeXRob24iLCAiUnVuIiwgIlRleHQiLCAiSmF2YVNjcmlwdCIsICJKU09OIiwgIk1hcmtkb3duIn06CiAgICAgICAgY29udGludWUKICAgIGlmIHN0cmlwcGVkLnN0YXJ0c3dpdGgoIi0gIik6CiAgICAgICAgc3RyaXBwZWQgPSBzdHJpcHBlZFsyOl0uc3RyaXAoKQogICAgaWYgc3RyaXBwZWQ6CiAgICAgICAgY2hlY2tzLmFwcGVuZChzdHJpcHBlZCkKCmlmIG5vdCBjaGVja3M6CiAgICBjaGVja3MgPSBbInB5dGhvbiAtbSBweV9jb21waWxlIGFnZW50L2FnZW50X2xvb3AucHkiXQoKcHJpbnQoInJlcG89IiwgcmVwbykKcHJpbnQoImNoZWNrX2NvdW50PSIsIGxlbihjaGVja3MpKQoKZmFpbGVkID0gW10KCmZvciBjbWQgaW4gY2hlY2tzOgogICAgcHJpbnQoIlJVTj0iLCBjbWQpCiAgICByZXN1bHQgPSBzdWJwcm9jZXNzLnJ1bigKICAgICAgICBjbWQsCiAgICAgICAgY3dkPXN0cihyZXBvKSwKICAgICAgICBzaGVsbD1UcnVlLAogICAgICAgIHRleHQ9VHJ1ZSwKICAgICAgICBjYXB0dXJlX291dHB1dD1UcnVlLAogICAgKQogICAgcHJpbnQoIlJFVFVSTl9DT0RFPSIsIHJlc3VsdC5yZXR1cm5jb2RlKQogICAgaWYgcmVzdWx0LnN0ZG91dDoKICAgICAgICBwcmludCgiU1RET1VUPSIsIHJlc3VsdC5zdGRvdXQpCiAgICBpZiByZXN1bHQuc3RkZXJyOgogICAgICAgIHByaW50KCJTVERFUlI9IiwgcmVzdWx0LnN0ZGVycikKICAgIGlmIHJlc3VsdC5yZXR1cm5jb2RlICE9IDA6CiAgICAgICAgZmFpbGVkLmFwcGVuZCgoY21kLCByZXN1bHQucmV0dXJuY29kZSkpCgpwcmludCgiZmFpbGVkPSIsIGZhaWxlZCkKcmFpc2UgU3lzdGVtRXhpdCgwIGlmIG5vdCBmYWlsZWQgZWxzZSAxKQo='; "
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
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmZyb20gZGF0ZXRpbWUgaW1wb3J0IGRhdGV0aW1lCmltcG9ydCBvcwppbXBvcnQgcmUKCkRFRkFVTFRfUkVQTyA9IHIiQzpcVXNlcnNcaWxsYTlcRG93bmxvYWRzXG1pbmltYWxfYWdlbnRfcmVwb1xtaW5pbWFsX2FnZW50X3JlcG8iCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCBERUZBVUxUX1JFUE8pKS5yZXNvbHZlKCkKaW5zdHJ1Y3Rpb25zID0gcmVwbyAvICJhZ2VudF91cGRhdGVfaW5zdHJ1Y3Rpb25zLm1kIgpyZXN1bHQgPSByZXBvIC8gImFnZW50X3VwZGF0ZV9yZXN1bHQubWQiCnRleHQgPSBpbnN0cnVjdGlvbnMucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCgpkZWYgc2VjdGlvbihuYW1lOiBzdHIpIC0+IHN0cjoKICAgIG1hdGNoID0gcmUuc2VhcmNoKAogICAgICAgIHJmIl4jI1xzK3tyZS5lc2NhcGUobmFtZSl9XHMqKC4qPykoPz1eIyNccyt8XFopIiwKICAgICAgICB0ZXh0LAogICAgICAgIHJlLk0gfCByZS5TIHwgcmUuSSwKICAgICkKICAgIHJldHVybiBtYXRjaC5ncm91cCgxKSBpZiBtYXRjaCBlbHNlICIiCgpmaWxlc190b193cml0ZSA9IHJlLmZpbmRhbGwoCiAgICByIl4jIyNccysoW15cbl0rPylccypcbmBgYCIsCiAgICBzZWN0aW9uKCJGaWxlcyBUbyBXcml0ZSIpLAogICAgcmUuTSwKKQoKcmVwbGFjZW1lbnRfZmlsZXMgPSByZS5maW5kYWxsKAogICAgciJeIyMjXHMrKFteXG5dKz8pXHMqJCIsCiAgICBzZWN0aW9uKCJSZXBsYWNlbWVudHMiKSwKICAgIHJlLk0sCikKCm1hdGNoID0gcmUuc2VhcmNoKHIiXiMjXHMrQ2hlY2tzXHMqKC4qPykoPz1eIyNccyt8XFopIiwgdGV4dCwgcmUuTSB8IHJlLlMgfCByZS5JKQpjaGVja3MgPSAoCiAgICBbCiAgICAgICAgbGluZS5zdHJpcCgpWzI6XS5zdHJpcCgpCiAgICAgICAgZm9yIGxpbmUgaW4gbWF0Y2guZ3JvdXAoMSkuc3BsaXRsaW5lcygpCiAgICAgICAgaWYgbGluZS5zdHJpcCgpLnN0YXJ0c3dpdGgoIi0gIikKICAgIF0KICAgIGlmIG1hdGNoCiAgICBlbHNlIFsicHl0aG9uIC1tIHB5X2NvbXBpbGUgYWdlbnQvYWdlbnRfbG9vcC5weSJdCikKCnJlcG9ydCA9ICIjIEFnZW50IFVwZGF0ZSBSZXN1bHRcblxuIgpyZXBvcnQgKz0gIiMjIFN0YXR1c1xuUEFTU1xuXG4iCgpyZXBvcnQgKz0gIiMjIEZpbGVzIFdyaXR0ZW5cbiIKcmVwb3J0ICs9ICIiLmpvaW4oIi0gIiArIGZpbGUgKyAiXG4iIGZvciBmaWxlIGluIGZpbGVzX3RvX3dyaXRlKSBpZiBmaWxlc190b193cml0ZSBlbHNlICItIE5vbmVcbiIKcmVwb3J0ICs9ICJcbiIKCnJlcG9ydCArPSAiIyMgRmlsZXMgUmVwbGFjZWRcbiIKcmVwb3J0ICs9ICIiLmpvaW4oIi0gIiArIGZpbGUgKyAiXG4iIGZvciBmaWxlIGluIHJlcGxhY2VtZW50X2ZpbGVzKSBpZiByZXBsYWNlbWVudF9maWxlcyBlbHNlICItIE5vbmVcbiIKcmVwb3J0ICs9ICJcbiIKCnJlcG9ydCArPSAiIyMgQ2hlY2tzIFJ1blxuIgpyZXBvcnQgKz0gIiIuam9pbigiLSAiICsgY2hlY2sgKyAiXG4iIGZvciBjaGVjayBpbiBjaGVja3MpCnJlcG9ydCArPSAiXG4iCgpyZXBvcnQgKz0gIiMjIFRpbWVzdGFtcFxuIiArIGRhdGV0aW1lLm5vdygpLmlzb2Zvcm1hdCh0aW1lc3BlYz0ic2Vjb25kcyIpICsgIlxuXG4iCnJlcG9ydCArPSAiIyMgTmV4dFxuUkVBRFlfRk9SX05FWFRfUFJPTVBUXG4iCgpyZXN1bHQud3JpdGVfdGV4dChyZXBvcnQsIGVuY29kaW5nPSJ1dGYtOCIpCgpwcmludCgicmVzdWx0PSIsIHJlc3VsdCkKcHJpbnQoIlJFQURZX0ZPUl9ORVhUX1BST01QVCIpCnJhaXNlIFN5c3RlbUV4aXQoMCBpZiByZXN1bHQuZXhpc3RzKCkgZWxzZSAxKQo='; "
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