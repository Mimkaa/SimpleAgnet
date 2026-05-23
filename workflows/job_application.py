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
                        "application_package.md",

                        "cover_letter.tex",
                        "cover_letter.aux",
                        "cover_letter.log",
                        "cover_letter.out",
                        "cover_letter.pdf",
                        "cover_letter_source_context.md",
                        "cover_letter_pdf_diagnostics.md",
                        "cover_letter_pdf_compile_result.md",
                        "cover_letter_pdf_verification.md",

                        "tailored_cv.tex",
                        "tailored_cv.aux",
                        "tailored_cv.log",
                        "tailored_cv.out",
                        "tailored_cv.pdf",
                        "tailored_cv_pdf_compile_result.md",
                        "tailored_cv_pdf_verification.md",
                        "tailored_cv_compile_diagnostic.md",
                        "final_application_package.md",
                    ],
                    "exclude_patterns": [
                        "generated_*",
                        "*_verification.md",
                        "job_application_*_review.md",
                        "application_package.md",

                        "cover_letter.*",
                        "cover_letter_*_diagnostics.md",
                        "cover_letter_*_context.md",
                        "cover_letter_pdf_*.md",

                        "repair_report_*.md",

                        "tailored_cv.*",
                        "tailored_cv_pdf_*.md",
                        "tailored_cv_*_diagnostic.md",
                        "tailored_cv_*_diagnostics.md",
                        "final_application_package.md",
                    ],
                    "outputs": ["job_application_input_inventory.md"],
                    "reason": (
                        "Collect the available local data for a job application workflow. "
                        "Read markdown and text files from the configured target project directory. "
                        "Missing expected files should be reported clearly instead of invented. "
                        "Generated files, verification files, previous review outputs, LaTeX outputs, "
                        "PDF outputs, repair reports, and diagnostic files should be excluded so they "
                        "do not pollute the next run. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Extract structured job application context",
                description=(
                    "Extract structured candidate, job, company, and missing-information "
                    "details from the local job application input inventory."
                ),
                inputs=["job_application_input_inventory.md"],
                outputs=["structured_job_application_context.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["job_application_input_inventory.md"],
                    "outputs": ["structured_job_application_context.md"],
                    "reason": (
                        "Extract a structured job application context from the input inventory. "
                        "Use only facts present in the local files. "
                        "Create sections exactly named: "
                        "## Candidate, ## Job, ## Company Notes, ## Extra Notes, ## Missing Information. "
                        "Under Candidate include name, education, skills, projects, experience, and languages. "
                        "Under Job include position, company, location, responsibilities, requirements, and nice-to-have items. "
                        "Under Missing Information list unknown contact details, availability, recipient, links, and application logistics. "
                        "Do not invent facts."
                    ),
                },
            ),

            Task(
                title="Create job application readiness report",
                description=(
                    "Analyze the discovered local inputs and explain what is available, "
                    "what is missing, and what can safely be drafted."
                ),
                inputs=[
                    "job_application_input_inventory.md",
                    "structured_job_application_context.md",
                ],
                outputs=["job_application_readiness_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "job_application_input_inventory.md",
                        "structured_job_application_context.md",
                    ],
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
                    "structured_job_application_context.md",
                    "job_application_readiness_report.md",
                ],
                outputs=["tailored_cover_letter.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "structured_job_application_context.md",
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
                    "structured_job_application_context.md",
                    "job_application_readiness_report.md",
                    "tailored_cover_letter.md",
                ],
                outputs=["job_application_final_review.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "structured_job_application_context.md",
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
                inputs=["cover_letter_verification_requirements.md"],
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

            Task(
                title="Create final application package",
                description=(
                    "Create a final application package artifact that combines the generated "
                    "cover letter, missing-information checklist, verification result, and final review summary."
                ),
                inputs=[
                    "structured_job_application_context.md",
                    "tailored_cover_letter.md",
                    "job_application_final_review.md",
                    "materialized_cover_letter_verification.md",
                ],
                outputs=["application_package.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "structured_job_application_context.md",
                        "tailored_cover_letter.md",
                        "job_application_final_review.md",
                        "materialized_cover_letter_verification.md",
                    ],
                    "outputs": ["application_package.md"],
                    "reason": (
                        "Create a clean final job application package. "
                        "The package should contain: "
                        "1. the final cover letter text, "
                        "2. a missing-information checklist before sending, "
                        "3. the verification result summary, "
                        "4. a short final review summary. "
                        "Use only facts from the input artifacts. "
                        "Do not invent new candidate, company, job, contact, or availability details. "
                        "Do not wrap the cover letter in markdown code fences."
                    ),
                },
            ),

            Task(
                title="Create LaTeX cover letter",
                description=(
                    "Create a LaTeX cover letter file from the tailored cover letter and "
                    "structured job application context."
                ),
                inputs=[
                    "structured_job_application_context.md",
                    "tailored_cover_letter.md",
                    "application_package.md",
                ],
                outputs=["cover_letter.tex"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "structured_job_application_context.md",
                        "tailored_cover_letter.md",
                        "application_package.md",
                    ],
                    "outputs": ["cover_letter.tex"],
                    "reason": (
                        "Create a clean standalone LaTeX cover letter. "
                        "Output only valid LaTeX source code, no markdown code fences and no explanations. "
                        "Use only this document class: \\documentclass[11pt,a4paper]{article}. "
                        "Do not use the letter document class. "
                        "Do not use \\begin{letter}, \\end{letter}, \\opening, \\closing, \\signature, or \\address. "
                        "Write the letter manually using flushleft blocks, bold text, normal paragraphs, and line breaks. "
                        "Use standard packages only: geometry, parskip, hyperref, enumitem if needed. "
                        "The document should contain the actual cover letter text. "
                        "Keep placeholders for missing contact details such as email, phone, address, date, "
                        "and hiring manager if they are not available. "
                        "Do not invent contact details, dates, links, availability, or company address. "
                        "Escape LaTeX special characters where needed. "
                        "Do not put placeholder text like [Candidate email] directly at the beginning of a line after a LaTeX line break. "
                        "Represent placeholders using \\textnormal{\\lbrack{}Email address\\rbrack{}} or normal text such as "
                        "Email address: \\textnormal{\\lbrack{}missing\\rbrack{}}. "
                        "Do not use raw square-bracket placeholders immediately after \\\\ because LaTeX may treat them as optional line-break arguments. "
                        "Prefer placeholders like \\textnormal{\\lbrack{}Date\\rbrack{}} instead of [Date]. "
                        "The result must be compilable by pdflatex with exit code 0."
                    ),
                },
            ),

            Task(
                title="Write LaTeX cover letter to target project",
                description=(
                    "Write the generated LaTeX cover letter into the target project folder."
                ),
                inputs=["cover_letter.tex"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "cover_letter.tex",
                    "root": "target_project",
                    "target_file": "cover_letter.tex",
                    "reason": (
                        "Materialize the LaTeX cover letter into the target project folder."
                    ),
                },
            ),

            Task(
                title="Compile LaTeX cover letter to PDF",
                description=(
                    "Compile the generated LaTeX cover letter into a PDF in the target project folder."
                ),
                inputs=["cover_letter.tex"],
                outputs=["cover_letter_pdf_compile_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \"from pathlib import Path; "
                        "[p.unlink() for p in [Path('cover_letter.aux'), Path('cover_letter.out'), Path('cover_letter.log')] if p.exists()]\" "
                        "&& pdflatex -interaction=nonstopmode -halt-on-error cover_letter.tex"
                    ),
                    "outputs": ["cover_letter_pdf_compile_result.md"],
                    "reason": (
                        "Compile cover_letter.tex into cover_letter.pdf using pdflatex."
                    ),
                },
            ),

            Task(
                title="Verify compiled cover letter PDF",
                description=(
                    "Verify that cover_letter.pdf was created in the target project folder."
                ),
                inputs=["cover_letter_pdf_compile_result.md"],
                outputs=["cover_letter_pdf_verification.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \"from pathlib import Path; "
                        "p=Path('cover_letter.pdf'); "
                        "print('exists=', p.exists()); "
                        "print('size=', p.stat().st_size if p.exists() else 0); "
                        "raise SystemExit(0 if p.exists() and p.stat().st_size > 0 else 1)\""
                    ),
                    "outputs": ["cover_letter_pdf_verification.md"],
                    "reason": (
                        "Verify that cover_letter.pdf exists and is not empty."
                    ),
                },
            ),

            Task(
                title="Create LaTeX tailored CV",
                description=(
                    "Create a tailored LaTeX CV from the structured job application context."
                ),
                inputs=[
                    "structured_job_application_context.md",
                    "job_application_readiness_report.md",
                    "application_package.md",
                ],
                outputs=["tailored_cv.tex"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "structured_job_application_context.md",
                        "job_application_readiness_report.md",
                        "application_package.md",
                    ],
                    "outputs": ["tailored_cv.tex"],
                    "reason": (
                        "Create a clean standalone LaTeX CV tailored to the job posting. "
                        "Output only valid LaTeX source code, no markdown code fences and no explanations. "
                        "Use only this document class: \\documentclass[11pt,a4paper]{article}. "
                        "Use standard packages only: geometry, parskip, hyperref, enumitem if needed. "
                        "The CV should contain only facts from the input artifacts. "
                        "Do not invent work experience, education, skills, contact details, links, grades, dates, or certifications. "
                        "It is allowed to reorder and emphasize existing skills and projects based on the job posting. "
                        "Include sections such as Profile, Education, Skills, Projects, Experience, and Languages if information is available. "
                        "For missing contact details, use safe LaTeX placeholders like \\textnormal{\\lbrack{}Email address\\rbrack{}}. "
                        "Do not use raw square-bracket placeholders like [Email address]. "
                        "Do not include a photo or image yet. "
                        "Escape LaTeX special characters where needed. "
                        "The result must be compilable by pdflatex with exit code 0."
                    ),
                },
            ),

            Task(
                title="Write LaTeX tailored CV to target project",
                description=(
                    "Write the generated LaTeX CV into the target project folder."
                ),
                inputs=["tailored_cv.tex"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "tailored_cv.tex",
                    "root": "target_project",
                    "target_file": "tailored_cv.tex",
                    "reason": (
                        "Materialize the tailored LaTeX CV into the target project folder."
                    ),
                },
            ),

            Task(
                title="Compile LaTeX tailored CV to PDF",
                description=(
                    "Compile the generated LaTeX CV into a PDF in the target project folder."
                ),
                inputs=["tailored_cv.tex"],
                outputs=["tailored_cv_pdf_compile_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \"from pathlib import Path; "
                        "[p.unlink() for p in [Path('tailored_cv.aux'), Path('tailored_cv.out'), Path('tailored_cv.log')] if p.exists()]\" "
                        "&& pdflatex -interaction=nonstopmode -halt-on-error tailored_cv.tex"
                    ),
                    "outputs": ["tailored_cv_pdf_compile_result.md"],
                    "reason": (
                        "Compile tailored_cv.tex into tailored_cv.pdf using pdflatex."
                    ),
                },
            ),

            Task(
                title="Verify compiled tailored CV PDF",
                description=(
                    "Verify that tailored_cv.pdf was created in the target project folder."
                ),
                inputs=["tailored_cv_pdf_compile_result.md"],
                outputs=["tailored_cv_pdf_verification.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \"from pathlib import Path; "
                        "p=Path('tailored_cv.pdf'); "
                        "print('exists=', p.exists()); "
                        "print('size=', p.stat().st_size if p.exists() else 0); "
                        "raise SystemExit(0 if p.exists() and p.stat().st_size > 0 else 1)\""
                    ),
                    "outputs": ["tailored_cv_pdf_verification.md"],
                    "reason": (
                        "Verify that tailored_cv.pdf exists and is not empty."
                    ),
                },
            ),

            Task(
                title="Create final application package index",
                description=(
                    "Create a final index of all generated application files and remaining manual steps."
                ),
                inputs=[
                    "application_package.md",
                    "job_application_final_review.md",
                    "cover_letter_pdf_compile_result.md",
                    "cover_letter_pdf_verification.md",
                    "tailored_cv_pdf_compile_result.md",
                    "tailored_cv_pdf_verification.md",
                ],
                outputs=["final_application_package.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "application_package.md",
                        "job_application_final_review.md",
                        "cover_letter_pdf_compile_result.md",
                        "cover_letter_pdf_verification.md",
                        "tailored_cv_pdf_compile_result.md",
                        "tailored_cv_pdf_verification.md",
                    ],
                    "outputs": ["final_application_package.md"],
                    "reason": (
                        "Create a final application package index. "
                        "This file should be a concise dashboard for the user. "
                        "Include a section named 'Generated files' listing the expected target-project files: "
                        "generated_cover_letter.md, cover_letter.tex, cover_letter.pdf, tailored_cv.tex, tailored_cv.pdf, "
                        "job_application_final_review.md, application_package.md, and final_application_package.md. "
                        "Include a section named 'PDF verification' summarizing whether the cover letter PDF and CV PDF were created. "
                        "Include a section named 'Before sending checklist' with manual checks such as filling contact details, "
                        "checking placeholders, reviewing PDFs visually, and attaching the correct PDFs. "
                        "Use only information from the input artifacts. "
                        "Do not invent contact details, recipient details, dates, links, or application submission instructions."
                    ),
                },
            ),

            Task(
                title="Write final application package index to target project",
                description=(
                    "Write the final application package index into the target project folder."
                ),
                inputs=["final_application_package.md"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "final_application_package.md",
                    "root": "target_project",
                    "target_file": "final_application_package.md",
                    "reason": (
                        "Materialize the final application package index into the target project folder."
                    ),
                },
            ),

            Task(
                title="Write final application package to target project",
                description=(
                    "Write the final application package artifact into the target project folder."
                ),
                inputs=["application_package.md"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "application_package.md",
                    "root": "target_project",
                    "target_file": "application_package.md",
                    "reason": (
                        "Materialize the final application package into the target project folder."
                    ),
                },
            ),
        ]