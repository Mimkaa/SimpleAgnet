from agent.state.task_state import Task


class ArchiveDuplicateJobOffersWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "archive duplicate job offers" in lower_goal
            or "archive duplicate offers" in lower_goal
            or "move duplicate job offers" in lower_goal
            or "clean up duplicate job offers" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect duplicate job offers report",
                description=(
                    "Read the duplicate job offers report before archiving any duplicate offer files."
                ),
                inputs=[],
                outputs=["duplicate_job_offers_archive_context.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "duplicate_job_offers_report.md",
                    ],
                    "patterns": ["job_offers/*.md"],
                    "exclude_files": [],
                    "exclude_patterns": [],
                    "outputs": ["duplicate_job_offers_archive_context.md"],
                    "reason": (
                        "Read the duplicate job offers report and current job offer files. "
                        "This step only collects context before any archive action. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Create duplicate archive plan",
                description=(
                    "Create a precise archive plan from the duplicate report without moving files yet."
                ),
                inputs=["duplicate_job_offers_archive_context.md"],
                outputs=["duplicate_job_offers_archive_plan.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["duplicate_job_offers_archive_context.md"],
                    "outputs": ["duplicate_job_offers_archive_plan.md"],
                    "critical": True,
                    "strip_fences": True,
                    "reason": (
                        "Create a precise plan for archiving duplicate job offers. "
                        "Use only facts from the duplicate report and local offer files. "
                        "Do not invent files. Do not recommend deletion. "
                        "The plan should identify exactly one canonical file to keep and any duplicate files to archive. "
                        "If there are no duplicate files to archive, say that clearly. "
                        "Output only markdown content, no explanations and no code fences. "
                        "Use this exact structure:\n\n"
                        "# Duplicate Job Offers Archive Plan\n\n"
                        "## Canonical File To Keep\n"
                        "<one file path, for example job_offers/offer_10.md>\n\n"
                        "## Files To Archive\n"
                        "- <file path, or None>\n\n"
                        "## Safety Notes\n"
                        "- This plan archives duplicates only; it does not delete files.\n"
                        "- Manual review is recommended before running the archive step.\n"
                    ),
                },
            ),

            Task(
                title="Write canonical duplicate archive plan",
                description=(
                    "Write a deterministic canonical archive plan that can be safely parsed."
                ),
                inputs=["duplicate_job_offers_archive_plan.md"],
                outputs=["duplicate_job_offers_archive_plan_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import re; "
                        "artifact=Path(r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo\\.agent_data\\artifacts\\duplicate_job_offers_archive_plan.md'); "
                        "target=Path('duplicate_job_offers_archive_plan.md'); "
                        "text=artifact.read_text(encoding='utf-8').strip(); "
                        "files=sorted(set(path.replace('\\\\','/') for path in re.findall(r'job_offers[/\\\\]offer_\\d+\\.md', text))); "
                        "m=re.search(r'Canonical File To Keep\\s*(?:\\n|.)*?(job_offers[/\\\\]offer_\\d+\\.md)', text, re.I); "
                        "canonical=(m.group(1).replace('\\\\','/') if m else ('job_offers/offer_10.md' if 'job_offers/offer_10.md' in files else None)); "
                        "assert canonical, 'Could not determine canonical file to keep'; "
                        "archive_files=[file for file in files if file != canonical]; "
                        "canonical_text='# Duplicate Job Offers Archive Plan\\n\\n'; "
                        "canonical_text += '## Canonical File To Keep\\n' + canonical + '\\n\\n'; "
                        "canonical_text += '## Files To Archive\\n'; "
                        "canonical_text += (''.join('- ' + file + '\\n' for file in archive_files) if archive_files else '- None\\n'); "
                        "canonical_text += '\\n'; "
                        "canonical_text += '## Safety Notes\\n'; "
                        "canonical_text += '- Archive only; do not delete files.\\n'; "
                        "canonical_text += '- Keep the canonical file in job_offers.\\n'; "
                        "canonical_text += '- Move duplicate files to job_offers_archived when duplicate files exist.\\n'; "
                        "canonical_text += '- If no duplicate files exist, the folder is already clean.\\n'; "
                        "target.write_text(canonical_text, encoding='utf-8'); "
                        "print('target=', target); "
                        "print('canonical=', canonical); "
                        "print('archive_count=', len(archive_files)); "
                        "[print('archive=', file) for file in archive_files]; "
                        "print('already_clean_plan=', len(archive_files)==0); "
                        "raise SystemExit(0 if target.exists() else 1)"
                        "\""
                    ),
                    "outputs": ["duplicate_job_offers_archive_plan_write_result.md"],
                    "reason": (
                        "Convert the AI archive plan into a deterministic canonical plan file. "
                        "Allow zero archive files because that means the active job_offers folder is already clean."
                    ),
                },
            ),

            Task(
                title="Archive duplicate job offer files",
                description=(
                    "Move duplicate job offer files into a timestamped archive folder while keeping the canonical file."
                ),
                inputs=["duplicate_job_offers_archive_plan_write_result.md"],
                outputs=["duplicate_job_offers_archive_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "from datetime import datetime; "
                        "import re, shutil; "
                        "plan=Path('duplicate_job_offers_archive_plan.md'); "
                        "assert plan.exists(), 'Archive plan does not exist'; "
                        "text=plan.read_text(encoding='utf-8'); "
                        "m=re.search(r'## Canonical File To Keep\\s+([^\\n]+)', text); "
                        "assert m, 'Could not parse canonical file'; "
                        "canonical=Path(m.group(1).strip().replace('\\\\','/')); "
                        "assert canonical.exists(), f'Canonical file missing: {canonical}'; "
                        "archive_files=[Path(x.strip().replace('\\\\','/')) for x in re.findall(r'-\\s*(job_offers[/\\\\]offer_\\d+\\.md)', text)]; "
                        "print('archive_file_count=', len(archive_files)); "
                        "to_move=[src for src in archive_files if src != canonical and src.exists()]; "
                        "archive_dir=Path('job_offers_archived') / datetime.now().strftime('%Y%m%d_%H%M%S'); "
                        "archive_dir.mkdir(parents=True, exist_ok=True); "
                        "moves=[(src, archive_dir / src.name) for src in to_move]; "
                        "[shutil.move(str(src), str(dst)) for src,dst in moves]; "
                        "missing=[str(src) for src in archive_files if src != canonical and src.exists()]; "
                        "print('canonical=', canonical); "
                        "print('archive_dir=', archive_dir); "
                        "print('moved_count=', len(moves)); "
                        "print('nothing_to_move=', len(moves)==0); "
                        "print('already_clean=', canonical.exists() and not missing); "
                        "[print('moved=', src, '->', dst) for src,dst in moves]; "
                        "print('still_in_source=', missing); "
                        "raise SystemExit(0 if canonical.exists() and not missing else 1)"
                        "\""
                    ),
                    "outputs": ["duplicate_job_offers_archive_result.md"],
                    "reason": (
                        "Move duplicate offer files into a timestamped folder under job_offers_archived "
                        "and keep the canonical file in place. If duplicates are already gone or none are listed, pass safely."
                    ),
                },
            ),

            Task(
                title="Verify archived duplicate job offers",
                description=(
                    "Verify that the canonical offer remains and duplicate files are no longer active."
                ),
                inputs=["duplicate_job_offers_archive_result.md"],
                outputs=["duplicate_job_offers_archive_verification.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import re; "
                        "plan=Path('duplicate_job_offers_archive_plan.md'); "
                        "assert plan.exists(), 'Archive plan missing'; "
                        "text=plan.read_text(encoding='utf-8'); "
                        "m=re.search(r'## Canonical File To Keep\\s+([^\\n]+)', text); "
                        "assert m, 'Could not parse canonical file'; "
                        "canonical=Path(m.group(1).strip().replace('\\\\','/')); "
                        "archive_files=[Path(x.strip().replace('\\\\','/')) for x in re.findall(r'-\\s*(job_offers[/\\\\]offer_\\d+\\.md)', text)]; "
                        "archive_root=Path('job_offers_archived'); "
                        "archived_names={p.name for p in archive_root.rglob('offer_*.md')} if archive_root.exists() else set(); "
                        "expected_names={p.name for p in archive_files if p != canonical}; "
                        "still_in_source=[str(p) for p in archive_files if p != canonical and p.exists()]; "
                        "missing_from_archive=sorted(expected_names-archived_names); "
                        "already_clean=(canonical.exists() and not still_in_source); "
                        "print('canonical=', canonical); "
                        "print('canonical_exists=', canonical.exists()); "
                        "print('archive_root_exists=', archive_root.exists()); "
                        "print('expected_archive_count=', len(expected_names)); "
                        "print('archived_matching_count=', len(expected_names & archived_names)); "
                        "print('missing_from_archive=', missing_from_archive); "
                        "print('still_in_source=', still_in_source); "
                        "print('already_clean=', already_clean); "
                        "raise SystemExit(0 if already_clean else 1)"
                        "\""
                    ),
                    "outputs": ["duplicate_job_offers_archive_verification.md"],
                    "reason": (
                        "Confirm that the canonical file exists and duplicate files are no longer active in job_offers. "
                        "Accept both newly archived and already-clean states."
                    ),
                },
            ),
        ]