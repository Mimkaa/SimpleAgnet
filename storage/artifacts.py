from pathlib import Path


class Artifacts:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str) -> Path:
        return self.directory / name

    def write_text(self, name: str, content: str) -> Path:
        path = self.path_for(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read_text(self, name: str) -> str:
        path = self.path_for(name)
        return path.read_text(encoding="utf-8")

    def exists(self, name: str) -> bool:
        return self.path_for(name).exists()

    def list_files(self):
        return [p.name for p in self.directory.iterdir() if p.is_file()]