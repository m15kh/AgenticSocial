from crewai import Agent, LLM


def create_twitter_poster(llm: LLM, tools: list) -> Agent:
    """Create and configure the Twitter posting agent"""
    return Agent(
        role="Twitter Bot Operator",
        goal="Use the Twitter Poster tool to post messages. Always execute the tool.",
        backstory=(
            "You are a Twitter bot operator. Your job is to use the Twitter Poster tool. "
            "You take the message from the writer and post it to Twitter. "
            "You MUST see a confirmation message with a tweet ID to know it worked."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
        max_iter=2,
        allow_delegation=False,
    )