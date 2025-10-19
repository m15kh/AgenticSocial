from crewai import Task, Agent


def create_twitter_task(agent: Agent, context_tasks: list, api_key: str, 
                       api_secret: str, access_token: str, access_token_secret: str) -> Task:
    """Create the Twitter posting task"""
    return Task(
        description=f"""
        Take the message from the previous task and post it to Twitter using the Twitter Poster tool.
        
        CRITICAL: You MUST actually USE the tool. Do not just describe using it.
        
        NOTE: Twitter has a 280 character limit. The tool will automatically create a thread if needed.
        
        Execute this action NOW:
        
        Tool: Twitter Poster
        Parameters:
        - message: [take the message from the writer - format it for Twitter]
        - api_key: {api_key}
        - api_secret: {api_secret}
        - access_token: {access_token}
        - access_token_secret: {access_token_secret}
        
        After using the tool, you will see a confirmation like:
        "✅ Successfully posted to Twitter! Tweet ID: [number]"
        
        That tweet ID is proof the post worked.
        """,
        agent=agent,
        expected_output="The exact confirmation message from the Twitter Poster tool with tweet ID",
        context=context_tasks,
    )