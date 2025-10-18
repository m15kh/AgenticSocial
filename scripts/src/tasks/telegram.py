from crewai import Task, Agent
from scripts.src.utils.template_loader import template_loader


def create_telegram_task(agent: Agent, context_tasks: list, bot_token: str, channel_id: str) -> Task:
    """Create the Telegram posting task"""
    
    description = template_loader.load(
        'telegram_poster',
        bot_token=bot_token,
        channel_id=channel_id
    )
    
    return Task(
        description=description,
        agent=agent,
        expected_output="The exact confirmation message from the Telegram Poster tool with format: '✅ Successfully posted to Telegram! Message ID: [actual number]'",
        context=context_tasks,
    )