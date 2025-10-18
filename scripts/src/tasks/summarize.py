from crewai import Task, Agent
from scripts.src.utils.template_loader import template_loader


def create_summarize_task(agent: Agent, url: str = None) -> Task:
    """Create the summarization task"""
    description = template_loader.load('researcher', url=url or '{url}')
    
    return Task(
        description=description,
        agent=agent,
        expected_output="A clear, concise summary in 3-4 paragraphs.",
    )