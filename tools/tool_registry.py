class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, handler):
        self._tools[name] = handler

    def has(self, name):
        """Return True if a tool with this name is registered."""
        return name in self._tools

    def run(self, name, task, action):
        if name not in self._tools:
            return {
                "ok": False,
                "message": f"Unknown tool: {name}",
            }

        return self._tools[name](task, action)
