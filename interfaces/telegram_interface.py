class TelegramInterface:
    '''
    Placeholder for your existing Telegram bots.

    Recommended flow:
    Telegram message
    -> this interface parses it
    -> calls AgentLoop methods
    -> sends response through your existing bot service
    '''
    def __init__(self, agent):
        self.agent = agent

    def handle_text(self, text: str):
        if text.startswith("/goal "):
            return self.agent.create_goal(text[len("/goal "):])
        if text == "/tasks":
            return self.agent.list_tasks()
        if text == "/next":
            return self.agent.next_task()
        return "Unknown Telegram command."
