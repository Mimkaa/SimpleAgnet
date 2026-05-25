from agent.state.task_state import Task


class AddPastedJobOfferWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "add pasted job offer" in lower_goal
            or "add job offer from file" in lower_goal
            or "add new job offer" in lower_goal
            or "import pasted job offer" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Verify pasted job offer input exists",
                description=(
                    "Check that the target project contains a pasted job offer input file."
                ),
                inputs=[],
                outputs=["new_job_offer_input_check.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "files=['new_job_offer.txt','new_job_offer.md','new_job_offer.html']; "
                        "existing=[f for f in files if Path(f).exists() and Path(f).read_text(encoding='utf-8', errors='ignore').strip()]; "
                        "print('existing_inputs=', existing); "
                        "raise SystemExit(0 if existing else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_input_check.md"],
                    "reason": (
                        "Verify that at least one pasted job offer input file exists before processing."
                    ),
                },
            ),

            Task(
                title="Inspect pasted job offer input",
                description=(
                    "Read pasted job offer text, markdown, or saved HTML from the target project."
                ),
                inputs=["new_job_offer_input_check.md"],
                outputs=["new_job_offer_source_snapshot.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "new_job_offer.txt",
                        "new_job_offer.md",
                        "new_job_offer.html",
                    ],
                    "patterns": [],
                    "exclude_files": [],
                    "exclude_patterns": [],
                    "outputs": ["new_job_offer_source_snapshot.md"],
                    "reason": (
                        "Read the pasted job offer input file. Missing variants are allowed "
                        "as long as at least one input file exists. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Normalize pasted job offer",
                description=(
                    "Convert the pasted job offer input into the standard local job offer format."
                ),
                inputs=["new_job_offer_source_snapshot.md"],
                outputs=["new_job_offer_normalized.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["new_job_offer_source_snapshot.md"],
                    "outputs": ["new_job_offer_normalized.md"],
                    "reason": (
                        "Normalize the pasted job offer into a clean markdown job offer file. "
                        "Use only facts from the input. "
                        "Ignore missing-file error blocks if at least one pasted job offer input file was readable. "
                        "Output only markdown content, no explanations and no code fences. "
                        "Use this exact structure:\n\n"
                        "# Offer\n\n"
                        "## Position\n"
                        "<position or unknown>\n\n"
                        "## Company\n"
                        "<company or unknown>\n\n"
                        "## Location\n"
                        "<location or unknown>\n\n"
                        "## Description\n"
                        "<clean summary of the role>\n\n"
                        "## Requirements\n"
                        "- <requirement>\n\n"
                        "## Nice to Have\n"
                        "- <nice-to-have>\n\n"
                        "Do not invent missing information. Use 'unknown' for missing company, position, or location."
                    ),
                },
            ),

            Task(
                title="Write normalized job offer to next offer file",
                description=(
                    "Write the normalized pasted job offer into the next job_offers/offer_N.md file."
                ),
                inputs=["new_job_offer_normalized.md"],
                outputs=["new_job_offer_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import re; "
                        "offers_dir=Path('job_offers'); "
                        "offers_dir.mkdir(exist_ok=True); "
                        "artifact=Path(r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo\\.agent_data\\artifacts\\new_job_offer_normalized.md'); "
                        "text=artifact.read_text(encoding='utf-8').strip(); "
                        "nums=[int(m.group(1)) for p in offers_dir.glob('offer_*.md') for m in [re.match(r'offer_(\\d+)\\.md$', p.name)] if m]; "
                        "next_num=(max(nums) if nums else 0)+1; "
                        "target=offers_dir / f'offer_{next_num}.md'; "
                        "target.write_text(text+'\\n', encoding='utf-8'); "
                        "print('written=', target); "
                        "print('chars=', len(text)); "
                        "print('next_num=', next_num); "
                        "raise SystemExit(0 if target.exists() and len(text) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_write_result.md"],
                    "reason": (
                        "Create the next numbered job offer file from the normalized pasted job offer artifact."
                    ),
                },
            ),

            Task(
                title="Verify added job offer",
                description=(
                    "Verify that the newest job offer file exists and contains the important job offer information."
                ),
                inputs=["new_job_offer_write_result.md"],
                outputs=["new_job_offer_verification.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import re; "
                        "offers=sorted(Path('job_offers').glob('offer_*.md'), key=lambda p: int(re.match(r'offer_(\\d+)\\.md$', p.name).group(1))); "
                        "assert offers, 'No offer files found'; "
                        "latest=offers[-1]; "
                        "text=latest.read_text(encoding='utf-8'); "
                        "required_any = ["
                            "('position', ['## Position', '# Job Offer:', '**Job title:**', '- **Job title:**', 'Job title:', 'Position:']), "
                            "('company', ['## Company', '**Company:**', '- **Company:**', 'Company:']), "
                            "('location', ['## Location', '**Location:**', '- **Location:**', 'Location:']), "
                            "('description', ['## Description', '## Role Summary', '## Company Overview']), "
                            "('requirements', ['## Requirements', '## Required Qualifications', '## Required Skills and Experience', '### Must-Have Requirements'])"
                            "]; "
                        "missing=[name for name, options in required_any if not any(option in text for option in options)]; "
                        "print('latest=', latest); "
                        "print('missing=', missing); "
                        "print('chars=', len(text)); "
                        "raise SystemExit(0 if not missing and len(text.strip()) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_verification.md"],
                    "reason": (
                        "Verify that the newest offer file contains the important information needed for ranking. "
                        "Accept either the strict standard headings or richer normalized headings produced by the analyzer."
                    ),
                },
            ),
        ]