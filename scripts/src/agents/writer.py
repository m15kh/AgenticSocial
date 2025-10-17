from crewai import Agent, LLM

def create_writer(llm: LLM) -> Agent:
    """Create and configure the social media writer agent"""
    return Agent(
        role="Social-Media Writer",
        goal="Craft engaging social media posts with proper Unicode emojis and formatting.",
        backstory=(
            "You are a creative social media expert who writes engaging content. "
            "You ALWAYS use real Unicode emojis (like 🚀 ⭐ 💡 🎯) NOT HTML entities. "
            "Your posts are well-formatted with line breaks and proper structure."
        ),
        llm=llm,
        verbose=True,
    )