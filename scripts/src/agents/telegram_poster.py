from crewai import Agent, LLM

def create_telegram_poster(llm: LLM, tools: list) -> Agent:
    """Create and configure the Telegram posting agent"""
    return Agent(
        role="Telegram Bot Operator",
        goal="Use the Telegram Poster tool to post messages. Always execute the tool, never just describe what you would do.",
        backstory=(
            "You are a Telegram bot operator. Your ONLY job is to use the Telegram Poster tool. "
            "You take the message from the writer and immediately use the tool to post it. "
            "You MUST see a confirmation message with a real message ID number to know it worked."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )