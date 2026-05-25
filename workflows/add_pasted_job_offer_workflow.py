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
                    "Convert the pasted job offer input into a clean intermediate job offer summary."
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
                        "Normalize the pasted job offer into a clean markdown job offer summary. "
                        "Use only facts from the input. "
                        "Ignore missing-file error blocks if at least one pasted job offer input file was readable. "
                        "Output only markdown content, no explanations and no code fences. "
                        "Extract the position, company, location, description, requirements, nice-to-have skills, "
                        "responsibilities, technologies, salary, workload, application instructions, contact details, "
                        "benefits, and any missing information. "
                        "Do not invent missing information. Use 'unknown' for missing company, position, or location."
                    ),
                },
            ),

            Task(
                title="Canonicalize normalized job offer",
                description=(
                    "Rewrite the normalized job offer so it starts with the required canonical headings."
                ),
                inputs=["new_job_offer_normalized.md"],
                outputs=["new_job_offer_canonical.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["new_job_offer_normalized.md"],
                    "outputs": ["new_job_offer_canonical.md"],
                    "reason": (
                        "Rewrite the normalized job offer into the required canonical format. "
                        "Use only facts from the input artifact. "
                        "Output only markdown content, no explanations and no code fences. "

                        "CRITICAL: The output MUST begin exactly with this structure and these exact headings:\n\n"
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
                        "- <nice-to-have or unknown>\n\n"

                        "After this required block, you may keep useful additional sections from the input, "
                        "such as Responsibilities, Technologies, Benefits, Salary, Workload, Application Instructions, "
                        "or Contact. "
                        "Do not rename, omit, or move the required canonical headings. "
                        "Do not invent missing information. Use 'unknown' for missing company, position, or location."
                    ),
                },
            ),

            Task(
                title="Write canonical job offer to next offer file",
                description=(
                    "Write the canonical pasted job offer into the next job_offers/offer_N.md file."
                ),
                inputs=["new_job_offer_canonical.md"],
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
                        "artifact=Path(r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo\\.agent_data\\artifacts\\new_job_offer_canonical.md'); "
                        "text=artifact.read_text(encoding='utf-8').strip(); "
                        "required=['# Offer','## Position','## Company','## Location','## Description','## Requirements','## Nice to Have']; "
                        "missing=[item for item in required if item not in text]; "
                        "find=lambda patterns: next((m.group(1).strip() for pat in patterns for m in [re.search(pat, text, re.S|re.I)] if m), 'unknown'); "
                        "position=find([r'\\|\\s*Job title\\s*\\|\\s*([^|\\n]+)\\|', r'\\|\\s*Position\\s*\\|\\s*([^|\\n]+)\\|', r'##\\s*Position\\s+(.+?)(?=\\n##|\\Z)', r'#\\s*Job Offer:?\\s*(.+?)(?=\\n|\\Z)']); "
                        "company=find([r'\\|\\s*Company\\s*\\|\\s*([^|\\n]+)\\|', r'##\\s*Company\\s+(.+?)(?=\\n##|\\Z)']); "
                        "location=find([r'\\|\\s*Location\\s*\\|\\s*([^|\\n]+)\\|', r'##\\s*Location\\s+(.+?)(?=\\n##|\\Z)']); "
                        "description=find([r'##\\s*Description\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Role Summary\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Company Summary\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Company Overview\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Overview\\s+(.+?)(?=\\n##|\\Z)']); "
                        "requirements=find([r'##\\s*Requirements\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Required Qualifications\\s+(.+?)(?=\\n##|\\Z)', r'##\\s*Required Skills and Experience\\s+(.+?)(?=\\n##|\\Z)', r'###\\s*Must-Have Requirements\\s+(.+?)(?=\\n##|\\n###|\\Z)']); "
                        "nice=find([r'##\\s*Nice to Have\\s+(.+?)(?=\\n##|\\Z)', r'###\\s*Nice-to-Have Requirements\\s+(.+?)(?=\\n##|\\n###|\\Z)', r'##\\s*Nice-to-Have Skills\\s+(.+?)(?=\\n##|\\Z)']); "
                        "canonical=('# Offer\\n\\n## Position\\n'+position+'\\n\\n## Company\\n'+company+'\\n\\n## Location\\n'+location+'\\n\\n## Description\\n'+description+'\\n\\n## Requirements\\n'+requirements+'\\n\\n## Nice to Have\\n'+nice+'\\n'); "
                        "final_text=text if not missing else canonical+'\\n\\n## Additional Details\\n\\n'+text; "
                        "missing2=[item for item in required if item not in final_text]; "
                        "assert not missing2, f'Final offer missing required standard headings: {missing2}'; "
                        "nums=[int(m.group(1)) for p in offers_dir.glob('offer_*.md') for m in [re.match(r'offer_(\\d+)\\.md$', p.name)] if m]; "
                        "next_num=(max(nums) if nums else 0)+1; "
                        "target=offers_dir / f'offer_{next_num}.md'; "
                        "target.write_text(final_text+'\\n', encoding='utf-8'); "
                        "print('written=', target); "
                        "print('chars=', len(final_text)); "
                        "print('next_num=', next_num); "
                        "print('wrapped=', bool(missing)); "
                        "raise SystemExit(0 if target.exists() and len(final_text) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_write_result.md"],
                    "reason": (
                        "Create the next numbered job offer file from the canonical pasted job offer artifact. "
                        "If the AI output does not contain the required canonical headings, deterministically wrap it "
                        "with a canonical top block and preserve the original output under Additional Details."
                    ),
                },
            ),

            Task(
                title="Verify added job offer",
                description=(
                    "Verify that the newest job offer file exists and has the required canonical structure."
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
                        "required=['# Offer','## Position','## Company','## Location','## Description','## Requirements','## Nice to Have']; "
                        "missing=[item for item in required if item not in text]; "
                        "print('latest=', latest); "
                        "print('missing=', missing); "
                        "print('chars=', len(text)); "
                        "raise SystemExit(0 if not missing and len(text.strip()) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_verification.md"],
                    "reason": (
                        "Verify that the newest offer file contains the canonical headings required for ranking."
                    ),
                },
            ),

            Task(
                title="Archive pasted job offer input",
                description=(
                    "Move the pasted job offer input file into an archive folder after successful import."
                ),
                inputs=["new_job_offer_verification.md"],
                outputs=["new_job_offer_archive_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "from datetime import datetime; "
                        "import re; "

                        "offer_rows=[(int(m.group(1)), p) for p in Path('job_offers').glob('offer_*.md') for m in [re.fullmatch(r'offer_(\\d+)\\.md', p.name)] if m]; "
                        "assert offer_rows, 'No numeric offer files found'; "
                        "latest=max(offer_rows, key=lambda item: item[0])[1]; "
                        "text=latest.read_text(encoding='utf-8'); "
                        "required=['# Offer','## Position','## Company','## Location','## Description','## Requirements','## Nice to Have']; "
                        "missing=[item for item in required if item not in text]; "
                        "assert not missing, f'Not archiving input because latest offer did not verify: {missing}'; "

                        "inputs=[Path('new_job_offer.txt'), Path('new_job_offer.md'), Path('new_job_offer.html')]; "
                        "existing=[p for p in inputs if p.exists() and p.read_text(encoding='utf-8', errors='ignore').strip()]; "
                        "archive_dir=Path('imported_job_inputs'); "
                        "archive_dir.mkdir(exist_ok=True); "
                        "stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); "
                        "archived=[]; "
                        "[archived.append((p, archive_dir / f'{p.stem}_{stamp}{p.suffix}')) for p in existing]; "
                        "[dst.write_text(src.read_text(encoding='utf-8', errors='ignore'), encoding='utf-8') for src, dst in archived]; "
                        "[src.unlink() for src, dst in archived]; "

                        "print('latest_offer=', latest); "
                        "print('missing=', missing); "
                        "print('archived_count=', len(archived)); "
                        "[print('archived=', src, '->', dst) for src, dst in archived]; "
                        "raise SystemExit(0 if archived else 1)"
                        "\""
                    ),
                    "outputs": ["new_job_offer_archive_result.md"],
                    "reason": (
                        "Archive the pasted job offer input only after independently confirming that the latest "
                        "created offer contains the canonical structure needed for ranking."
                    ),
                },
            ),
        ]