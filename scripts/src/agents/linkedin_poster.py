from crewai import Agent, LLM


def create_linkedin_poster(llm: LLM, tools: list) -> Agent:
    """Create and configure the LinkedIn posting agent"""
    return Agent(
        role="LinkedIn Bot Operator",
        goal="Use the LinkedIn Poster tool and report the EXACT result it returns",
        backstory=(
            "You are a LinkedIn bot operator. You MUST use the LinkedIn Poster tool. "
            "After using the tool, you MUST report the EXACT message the tool returns. "
            "NEVER make up post IDs or pretend the post succeeded."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
        max_iter=2,
        allow_delegation=False,
    )