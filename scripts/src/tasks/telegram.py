from crewai import Task, Agent

def create_telegram_task(agent: Agent, context_tasks: list, bot_token: str, channel_id: str) -> Task:
    """Create the Telegram posting task"""
    return Task(
        description=f"""
        Take the message from the previous task and post it to Telegram using the Telegram Poster tool.
        
        CRITICAL: You MUST actually USE the tool. Do not just describe using it.
        
        Execute this action NOW:
        
        Tool: Telegram Poster
        Parameters:
        - message: [take the EXACT message from the writer - the complete formatted text]
        - bot_token: {bot_token}
        - channel_id: {channel_id}
        
        After using the tool, you will see a confirmation like:
        "✅ Successfully posted to Telegram! Message ID: [number]"
        
        That message ID is proof the post worked.
        """,
        agent=agent,
        expected_output="The exact confirmation message from the Telegram Poster tool with format: '✅ Successfully posted to Telegram! Message ID: [actual number]'",
        context=context_tasks,
    )