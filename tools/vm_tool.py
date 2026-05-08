class VMTool:
    name = "vm"

    def run(self, action: str, **kwargs):
        return {
            "ok": False,
            "message": "VMTool placeholder. Add VirtualBox/SSH/UTM control here.",
            "action": action,
            "kwargs": kwargs,
        }
