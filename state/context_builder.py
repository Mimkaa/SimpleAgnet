class ContextBuilder:
    def build(self, task, memory=None, recent_events=None):
        memory = memory or {}
        recent_events = recent_events or []
        return {
            "task": task.to_dict(),
            "memory": memory,
            "recent_events": recent_events,
        }
