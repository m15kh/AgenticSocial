from crewai import Task, Agent

def create_social_task(agent: Agent, context_tasks: list) -> Task:
    """Create the social media posting task"""
    return Task(
        description="Write a single message (max 4096 chars) suitable for posting in a Telegram channel.",
        agent=agent,
        expected_output="One engaging Telegram channel message, concise and informative.",
        context=context_tasks,
    )