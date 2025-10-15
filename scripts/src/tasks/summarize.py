from crewai import Task, Agent

def create_summarize_task(agent: Agent) -> Task:
    """Create the summarization task"""
    return Task(
        description="Fetch and summarize the webpage at: {url}",
        agent=agent,
        expected_output="A clear, concise summary in 3 paragraphs.",
    )