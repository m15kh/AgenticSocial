from crewai import Task, Agent
from scripts.src.utils.template_loader import template_loader


def create_social_task(agent: Agent, context_tasks: list, source_url: str, social_links: dict) -> Task:
    """Create the social media posting task"""
    
    description = template_loader.load(
        'writer',
        source_url=source_url,
        twitter_url=social_links.get('twitter', ''),
        linkedin_url=social_links.get('linkedin', ''),
        youtube_url=social_links.get('youtube', ''),
        telegram_url=social_links.get('telegram_public', '')
    )
    
    return Task(
        description=description,
        agent=agent,
        expected_output="A simple, conversational Telegram post with HTML formatting, clickable links to article and social media.",
        context=context_tasks,
    )