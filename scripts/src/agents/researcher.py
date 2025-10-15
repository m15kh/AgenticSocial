from crewai import Agent, LLM

def create_researcher(llm: LLM, tools: list) -> Agent:
    """Create and configure the researcher agent"""
    return Agent(
        role="Web Researcher",
        goal="Summarize the content of a given website link.",
        backstory="You are an expert at extracting the key insights from any article or webpage.",
        tools=tools,
        llm=llm,
        verbose=True,
    )