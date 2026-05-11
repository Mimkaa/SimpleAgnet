from pathlib import Path
import argparse

def guess_language(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    return {
        ".py": "python",
        ".json": "json",
        ".md": "markdown",
        ".java": "java",
        ".js": "javascript",
        ".html": "html",
        ".css": "css",
        ".xml": "xml",
        ".txt": "text",
    }.get(suffix, "text")


def make_snapshot(root_dir, files, output_path):
    root_dir = Path(root_dir).resolve()
    output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    out = [
        "# Core Source Snapshot\n",
        "Target project directory:\n",
        "```text",
        str(root_dir),
        "```\n",
    ]

    for file in files:
        path = root_dir / file
        lang = guess_language(file)

        out.append(f"\n# FILE: {file}\n")
        out.append("Target path:\n")
        out.append("```text")
        out.append(str(path))
        out.append("```\n")

        if not path.exists():
            out.append("```text\nMISSING FILE\n```")
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            out.append(f"```text\nERROR READING FILE: {e}\n```")
            continue

        out.append(f"```{lang}")
        out.append(content)
        out.append("```")

    output_path.write_text("\n".join(out), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Project folder to read files from")
    parser.add_argument("files", nargs="+", help="Files to include in snapshot")
    parser.add_argument(
        "-o",
        "--output",
        default=".agent_data/artifacts/core_source_snapshot.md",
        help="Where to write the snapshot",
    )

    args = parser.parse_args()

    result = make_snapshot(args.root, args.files, args.output)
    print(f"Snapshot written to {result}")