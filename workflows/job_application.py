from agent.state.task_state import Task


class JobApplicationWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "job application" in lower_goal
            or "apply to job" in lower_goal
            or "application" in lower_goal
            or "cover letter" in lower_goal
            or "resume" in lower_goal
            or "cv" in lower_goal
            or "internship" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect local job application inputs",
                description=(
                    "Look inside the target project directory for local job application "
                    "materials such as CV, resume, candidate profile, job posting, "
                    "company notes, or previous cover letters."
                ),
                inputs=[],
                outputs=["job_application_input_inventory.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "cv.md",
                        "cv.txt",
                        "resume.md",
                        "resume.txt",
                        "profile.md",
                        "profile.txt",
                        "candidate_profile.md",
                        "candidate_profile.txt",
                        "job_posting.md",
                        "job_posting.txt",
                        "company_notes.md",
                        "company_notes.txt",
                        "cover_letter.md",
                        "cover_letter.txt",
                    ],
                    "patterns": [
                        "*.md",
                        "*.txt",
                    ],
                    "exclude_files": [
                        "generated_cover_letter.md",
                        "job_application_final_review.md",
                    ],
                    "exclude_patterns": [
                        "generated_*",
                        "*_verification.md",
                        "job_application_*_review.md",
                    ],
                    "outputs": ["job_application_input_inventory.md"],
                    "reason": (
                        "Collect the available local data for a job application workflow. "
                        "Read markdown and text files from the configured target project directory. "
                        "Missing expected files should be reported clearly instead of invented. "
                        "Generated files, verification files, and previous review outputs should be excluded "
                        "so they do not pollute the next run. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),
            Task(
                title="Create job application readiness report",
                description=(
                    "Analyze the discovered local inputs and explain what is available, "
                    "what is missing, and what can safely be drafted."
                ),
                inputs=["job_application_input_inventory.md"],
                outputs=["job_application_readiness_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["job_application_input_inventory.md"],
                    "outputs": ["job_application_readiness_report.md"],
                    "reason": (
                        "Create a readiness report for the job application request. "
                        "Explain which inputs are available, which are missing, and whether "
                        "a tailored cover letter can be drafted. "
                        "Do not invent missing job description, CV, resume, company, or candidate profile details. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),
            Task(
                title="Draft tailored cover letter",
                description=(
                    "Use the available CV/profile and job posting data to draft a tailored "
                    "cover letter. If required information is missing, write a partial draft "
                    "with clear placeholders."
                ),
                inputs=[
                    "job_application_input_inventory.md",
                    "job_application_readiness_report.md",
                ],
                outputs=["tailored_cover_letter.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "job_application_input_inventory.md",
                        "job_application_readiness_report.md",
                    ],
                    "outputs": ["tailored_cover_letter.md"],
                    "reason": (
                        "Draft a job cover letter using only available local data. "
                        "Use the CV/profile information and the job posting if they are available. "
                        "Do not invent work experience, education, skills, company facts, or job requirements. "
                        "Use clear placeholders for missing information. "
                        "The tone should be professional, honest, motivated, and not exaggerated. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),
            Task(
                title="Review final job application draft",
                description=(
                    "Review the tailored cover letter and readiness report for missing details, "
                    "unsupported claims, and consistency with the available local data."
                ),
                inputs=[
                    "job_application_input_inventory.md",
                    "job_application_readiness_report.md",
                    "tailored_cover_letter.md",
                ],
                outputs=["job_application_final_review.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "job_application_input_inventory.md",
                        "job_application_readiness_report.md",
                        "tailored_cover_letter.md",
                    ],
                    "outputs": ["job_application_final_review.md"],
                    "reason": (
                        "Review the final job application draft. "
                        "Check for unsupported claims, missing placeholders, weak wording, "
                        "and inconsistencies with the available local input files. "
                        "Do not add new facts. Only review and suggest improvements based on the artifacts."
                    ),
                },
            ),
            Task(
                title="Extract cover letter verification requirements",
                description=(
                    "Extract dynamic verification requirements from the generated cover letter "
                    "and readiness report, so the materialized file can be checked without "
                    "hardcoded candidate, company, or job-title strings."
                ),
                inputs=[
                    "job_application_readiness_report.md",
                    "tailored_cover_letter.md",
                ],
                outputs=["cover_letter_verification_requirements.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "job_application_readiness_report.md",
                        "tailored_cover_letter.md",
                    ],
                    "outputs": ["cover_letter_verification_requirements.md"],
                    "reason": (
                        "Create simple verification requirements for the generated cover letter. "
                        "The output must use exactly this format and no other sections:\n\n"
                        "# Cover Letter Verification Requirements\n\n"
                        "## Must contain\n"
                        "- <short exact string from the cover letter>\n"
                        "- <short exact string from the cover letter>\n"
                        "- <short exact string from the cover letter>\n\n"
                        "Rules:\n"
                        "- Include only exact strings that already appear in tailored_cover_letter.md.\n"
                        "- Include 5 to 10 short strings.\n"
                        "- Prefer candidate name, company name, position title, university, major skills, and project names.\n"
                        "- Do not write explanations.\n"
                        "- Do not write tables.\n"
                        "- Do not write dynamic variable names like {candidate_name}.\n"
                        "- Do not describe how verification should work.\n"
                        "- Only produce the markdown section '## Must contain' with bullet points."
                    ),
                },
            ),
            Task(
                title="Write cover letter to target project",
                description=(
                    "Write the generated tailored cover letter artifact into the target "
                    "job application project folder as a real markdown file."
                ),
                inputs=["tailored_cover_letter.md"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "tailored_cover_letter.md",
                    "root": "target_project",
                    "target_file": "generated_cover_letter.md",
                    "reason": (
                        "Materialize the generated cover letter artifact into the target "
                        "project folder so it can be used outside the agent artifact store."
                    ),
                },
            ),

            Task(
                title="Verify materialized cover letter file",
                description=(
                    "Verify that the generated cover letter was written into the target "
                    "project folder and contains expected job application content."
                ),
                inputs=[],
                outputs=["materialized_cover_letter_verification.md"],
                tool_hint="verify_target_file",
                kind="normal",
                action={
                    "tool": "verify_target_file",
                    "root": "target_project",
                    "target_file": "generated_cover_letter.md",
                    "must_contain_from_artifact": "cover_letter_verification_requirements.md",
                    "must_contain": [],
                    "outputs": ["materialized_cover_letter_verification.md"],
                    "reason": (
                        "Confirm that the generated cover letter exists in the target project "
                        "and contains the expected application-specific content."
                    ),
                },
            ),

            Task(
                title="Write final review to target project",
                description=(
                    "Write the final job application review artifact into the target "
                    "job application project folder as a real markdown file."
                ),
                inputs=["job_application_final_review.md"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "job_application_final_review.md",
                    "root": "target_project",
                    "target_file": "job_application_final_review.md",
                    "reason": (
                        "Materialize the final review artifact into the target project folder."
                    ),
                },
            ),
        ]