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
                        "python -c \""
                        "from pathlib import Path; "
                        "import base64; "
                        "script=Path('.agent_data/apply_agent_update_instructions.py'); "
                        "script.parent.mkdir(parents=True, exist_ok=True); "
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBvcwppbXBvcnQgcmUKCkRFRkFVTFRfUkVQTyA9IHIiQzpcVXNlcnNcaWxsYTlcRG93bmxvYWRzXG1pbmltYWxfYWdlbnRfcmVwb1xtaW5pbWFsX2FnZW50X3JlcG8iCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCBERUZBVUxUX1JFUE8pKS5yZXNvbHZlKCkKaW5zdHJ1Y3Rpb25zID0gcmVwbyAvICJhZ2VudF91cGRhdGVfaW5zdHJ1Y3Rpb25zLm1kIgp0ZXh0ID0gaW5zdHJ1Y3Rpb25zLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQoKZGVmIHZhbGlkYXRlX3RhcmdldChyYXdfcGF0aDogc3RyKSAtPiBQYXRoOgogICAgcmVsID0gcmF3X3BhdGguc3RyaXAoKS5yZXBsYWNlKCJcXCIsICIvIikKICAgIGFzc2VydCByZWwsICJFbXB0eSB0YXJnZXQgcGF0aCBpcyBub3QgYWxsb3dlZCIKICAgIGFzc2VydCBub3QgcmVsLnN0YXJ0c3dpdGgoIi8iKSwgZiJBYnNvbHV0ZSBwYXRocyBhcmUgbm90IGFsbG93ZWQ6IHtyZWx9IgogICAgYXNzZXJ0ICIuLiIgbm90IGluIFBhdGgocmVsKS5wYXJ0cywgZiJQYXJlbnQgZGlyZWN0b3J5IHRyYXZlcnNhbCBpcyBub3QgYWxsb3dlZDoge3JlbH0iCgogICAgdGFyZ2V0ID0gKHJlcG8gLyByZWwpLnJlc29sdmUoKQogICAgYXNzZXJ0IHN0cih0YXJnZXQpLnN0YXJ0c3dpdGgoc3RyKHJlcG8pKSwgZiJUYXJnZXQgZXNjYXBlcyByZXBvOiB7dGFyZ2V0fSIKICAgIGFzc2VydCAiLmVudiIgbm90IGluIHRhcmdldC5uYW1lLmxvd2VyKCksIGYiUmVmdXNpbmcgdG8gZWRpdCBlbnYvc2VjcmV0cyBmaWxlOiB7dGFyZ2V0fSIKICAgIHJldHVybiB0YXJnZXQKCmRlZiBzZWN0aW9uKG5hbWU6IHN0cikgLT4gc3RyOgogICAgbWF0Y2ggPSByZS5zZWFyY2goCiAgICAgICAgcmYiXiMjXHMre3JlLmVzY2FwZShuYW1lKX1ccyooLio/KSg/PV4jI1xzK3xcWikiLAogICAgICAgIHRleHQsCiAgICAgICAgcmUuTSB8IHJlLlMgfCByZS5JLAogICAgKQogICAgcmV0dXJuIG1hdGNoLmdyb3VwKDEpIGlmIG1hdGNoIGVsc2UgIiIKCmZpbGVzX3RvX3dyaXRlX3NlY3Rpb24gPSBzZWN0aW9uKCJGaWxlcyBUbyBXcml0ZSIpCnJlcGxhY2VtZW50c19zZWN0aW9uID0gc2VjdGlvbigiUmVwbGFjZW1lbnRzIikKCndyaXR0ZW4gPSBbXQpyZXBsYWNlZCA9IFtdCgp3cml0ZV9wYXR0ZXJuID0gcmUuY29tcGlsZSgKICAgIHIiXiMjI1xzKyhbXlxuXSs/KVxzKlxuYGBgW15cbl0qXG4oLio/KVxuYGBgIiwKICAgIHJlLk0gfCByZS5TLAopCgpmb3IgcmF3X3BhdGgsIGNvbnRlbnQgaW4gd3JpdGVfcGF0dGVybi5maW5kYWxsKGZpbGVzX3RvX3dyaXRlX3NlY3Rpb24pOgogICAgdGFyZ2V0ID0gdmFsaWRhdGVfdGFyZ2V0KHJhd19wYXRoKQogICAgdGFyZ2V0LnBhcmVudC5ta2RpcihwYXJlbnRzPVRydWUsIGV4aXN0X29rPVRydWUpCiAgICB0YXJnZXQud3JpdGVfdGV4dChjb250ZW50LnJzdHJpcCgpICsgIlxuIiwgZW5jb2Rpbmc9InV0Zi04IikKICAgIHdyaXR0ZW4uYXBwZW5kKHRhcmdldCkKCmZpbGVfYmxvY2tzID0gcmUuY29tcGlsZSgKICAgIHIiXiMjI1xzKyhbXlxuXSs/KVxzKlxuKC4qPykoPz1eIyMjXHMrfFxaKSIsCiAgICByZS5NIHwgcmUuUywKKQoKcGFpcl9wYXR0ZXJuID0gcmUuY29tcGlsZSgKICAgIHIiIyMjI1xzK1JlcGxhY2VccypcbmBgYFteXG5dKlxuKC4qPylcbmBgYFxzKiMjIyNccytXaXRoXHMqXG5gYGBbXlxuXSpcbiguKj8pXG5gYGAiLAogICAgcmUuUyB8IHJlLkksCikKCmZvciByYXdfcGF0aCwgYm9keSBpbiBmaWxlX2Jsb2Nrcy5maW5kYWxsKHJlcGxhY2VtZW50c19zZWN0aW9uKToKICAgIHRhcmdldCA9IHZhbGlkYXRlX3RhcmdldChyYXdfcGF0aCkKICAgIGFzc2VydCB0YXJnZXQuZXhpc3RzKCksIGYiUmVwbGFjZW1lbnQgdGFyZ2V0IGRvZXMgbm90IGV4aXN0OiB7dGFyZ2V0fSIKCiAgICBwYWlycyA9IHBhaXJfcGF0dGVybi5maW5kYWxsKGJvZHkpCiAgICBhc3NlcnQgcGFpcnMsIGYiTm8gcmVwbGFjZW1lbnQgcGFpcnMgZm91bmQgZm9yIHtyYXdfcGF0aH0iCgogICAgY3VycmVudCA9IHRhcmdldC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKCiAgICBmb3Igb2xkLCBuZXcgaW4gcGFpcnM6CiAgICAgICAgb2xkID0gb2xkLnJzdHJpcCgpCiAgICAgICAgbmV3ID0gbmV3LnJzdHJpcCgpCgogICAgICAgIGNvdW50ID0gY3VycmVudC5jb3VudChvbGQpCiAgICAgICAgYXNzZXJ0IGNvdW50ID09IDEsICgKICAgICAgICAgICAgZiJFeHBlY3RlZCBleGFjdGx5IG9uZSBtYXRjaCBpbiB7cmF3X3BhdGh9LCBmb3VuZCB7Y291bnR9LiAiCiAgICAgICAgICAgICJVc2UgYSBsYXJnZXIgZXhhY3Qgb2xkIGJsb2NrIGlmIHRoZSBtYXRjaCBpcyBhbWJpZ3VvdXMuIgogICAgICAgICkKCiAgICAgICAgY3VycmVudCA9IGN1cnJlbnQucmVwbGFjZShvbGQsIG5ldywgMSkKICAgICAgICByZXBsYWNlZC5hcHBlbmQodGFyZ2V0KQoKICAgIHRhcmdldC53cml0ZV90ZXh0KGN1cnJlbnQsIGVuY29kaW5nPSJ1dGYtOCIpCgpwcmludCgicmVwbz0iLCByZXBvKQpwcmludCgid3JpdHRlbl9jb3VudD0iLCBsZW4od3JpdHRlbikpCmZvciBwYXRoIGluIHdyaXR0ZW46CiAgICBwcmludCgid3JpdHRlbj0iLCBwYXRoKQoKcHJpbnQoInJlcGxhY2VtZW50X2NvdW50PSIsIGxlbihyZXBsYWNlZCkpCmZvciBwYXRoIGluIHJlcGxhY2VkOgogICAgcHJpbnQoInJlcGxhY2VkPSIsIHBhdGgpCgppZiBub3Qgd3JpdHRlbiBhbmQgbm90IHJlcGxhY2VkOgogICAgcHJpbnQoImluc3RydWN0aW9ucz0iLCBpbnN0cnVjdGlvbnMpCiAgICBwcmludCgiY2hhcnM9IiwgbGVuKHRleHQpKQogICAgcHJpbnQoImZpcnN0XzUwMF9jaGFycz0iKQogICAgcHJpbnQodGV4dFs6NTAwXSkKICAgIHJhaXNlIFN5c3RlbUV4aXQoCiAgICAgICAgIk5vIHdyaXRlcyBvciByZXBsYWNlbWVudHMgZm91bmQuIEV4cGVjdGVkICMjIEZpbGVzIFRvIFdyaXRlIG9yICMjIFJlcGxhY2VtZW50cy4iCiAgICApCgpyYWlzZSBTeXN0ZW1FeGl0KDApCg=='; "
                        "script.write_text(base64.b64decode(code_b64).decode('utf-8'), encoding='utf-8'); "
                        "print('script=', script)"
                        "\" "
                        "&& python .agent_data/apply_agent_update_instructions.py"
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
                        "code_b64='ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBvcwppbXBvcnQgcmUKaW1wb3J0IHN1YnByb2Nlc3MKCkRFRkFVTFRfUkVQTyA9IHIiQzpcVXNlcnNcaWxsYTlcRG93bmxvYWRzXG1pbmltYWxfYWdlbnRfcmVwb1xtaW5pbWFsX2FnZW50X3JlcG8iCnJlcG8gPSBQYXRoKG9zLmVudmlyb24uZ2V0KCJBR0VOVF9SRVBPX1JPT1QiLCBERUZBVUxUX1JFUE8pKS5yZXNvbHZlKCkKaW5zdHJ1Y3Rpb25zID0gcmVwbyAvICJhZ2VudF91cGRhdGVfaW5zdHJ1Y3Rpb25zLm1kIgp0ZXh0ID0gaW5zdHJ1Y3Rpb25zLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiKQoKbWF0Y2ggPSByZS5zZWFyY2gociJeIyNccytDaGVja3NccyooLio/KSg/PV4jI1xzK3xcWikiLCB0ZXh0LCByZS5NIHwgcmUuUyB8IHJlLkkpCmNoZWNrcyA9IFtdCmlmIG1hdGNoOgogICAgY2hlY2tzID0gWwogICAgICAgIGxpbmUuc3RyaXAoKVsyOl0uc3RyaXAoKQogICAgICAgIGZvciBsaW5lIGluIG1hdGNoLmdyb3VwKDEpLnNwbGl0bGluZXMoKQogICAgICAgIGlmIGxpbmUuc3RyaXAoKS5zdGFydHN3aXRoKCItICIpCiAgICBdCgppZiBub3QgY2hlY2tzOgogICAgY2hlY2tzID0gWyJweXRob24gLW0gcHlfY29tcGlsZSBhZ2VudC9hZ2VudF9sb29wLnB5Il0KCnByaW50KCJyZXBvPSIsIHJlcG8pCnByaW50KCJjaGVja19jb3VudD0iLCBsZW4oY2hlY2tzKSkKCmZhaWxlZCA9IFtdCgpmb3IgY21kIGluIGNoZWNrczoKICAgIHByaW50KCJSVU49IiwgY21kKQogICAgcmVzdWx0ID0gc3VicHJvY2Vzcy5ydW4oCiAgICAgICAgY21kLAogICAgICAgIGN3ZD1zdHIocmVwbyksCiAgICAgICAgc2hlbGw9VHJ1ZSwKICAgICAgICB0ZXh0PVRydWUsCiAgICAgICAgY2FwdHVyZV9vdXRwdXQ9VHJ1ZSwKICAgICkKICAgIHByaW50KCJSRVRVUk5fQ09ERT0iLCByZXN1bHQucmV0dXJuY29kZSkKICAgIGlmIHJlc3VsdC5zdGRvdXQ6CiAgICAgICAgcHJpbnQoIlNURE9VVD0iLCByZXN1bHQuc3Rkb3V0KQogICAgaWYgcmVzdWx0LnN0ZGVycjoKICAgICAgICBwcmludCgiU1RERVJSPSIsIHJlc3VsdC5zdGRlcnIpCiAgICBpZiByZXN1bHQucmV0dXJuY29kZSAhPSAwOgogICAgICAgIGZhaWxlZC5hcHBlbmQoKGNtZCwgcmVzdWx0LnJldHVybmNvZGUpKQoKcHJpbnQoImZhaWxlZD0iLCBmYWlsZWQpCnJhaXNlIFN5c3RlbUV4aXQoMCBpZiBub3QgZmFpbGVkIGVsc2UgMSkK'; "
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