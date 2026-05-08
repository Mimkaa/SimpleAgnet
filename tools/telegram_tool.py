class TelegramTool:
    '''
    Placeholder.

    Keep your existing Telegram bots.
    This tool should become the adapter that sends messages to them.
    '''
    name = "telegram"

    def run(self, chat: str, message: str):
        return {
            "ok": False,
            "message": "TelegramTool is a placeholder. Wire this to Telethon or python-telegram-bot.",
            "chat": chat,
            "text": message,
        }
