from crewai import Agent, LLM

def create_writer(llm: LLM) -> Agent:
    """Create and configure the social media writer agent"""
    return Agent(
        role="Social-Media Writer",
        goal="Craft engaging social media posts from summaries.",
        backstory="You are a creative writer skilled at making short, viral posts.",
        llm=llm,
        verbose=True,
    )