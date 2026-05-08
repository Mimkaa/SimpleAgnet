import os
from openai import OpenAI


class OpenAIArtifactAnalyzer:
    def __init__(self, model: str | None = None):
        self.client = OpenAI()
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-5.5")

    def analyze(self, task, input_contents: dict[str, str], output_name: str) -> str:
        input_text = self._format_inputs(input_contents)

        prompt = f"""
You are analyzing project artifacts for a local agent system.

Task title:
{task.title}

Task description:
{task.description}

Desired output artifact:
{output_name}

Input artifacts:
{input_text}

Create a useful Markdown artifact.

Rules:
- Output Markdown only.
- Be specific.
- Do not invent files that are not mentioned.
- If the input is insufficient, clearly say what is missing.
- Keep it practical and useful for the next task.
"""

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return response.output_text

    def _format_inputs(self, input_contents: dict[str, str]) -> str:
        parts = []

        for name, content in input_contents.items():
            parts.append(
                f"## Artifact: {name}\n\n"
                f"```text\n{content}\n```"
            )

        return "\n\n".join(parts)