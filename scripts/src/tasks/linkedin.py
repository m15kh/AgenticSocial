from crewai import Task, Agent


def create_linkedin_task(
    agent: Agent, 
    context_tasks: list,
    access_token: str, 
    author_urn: str,
    source_url: str = None,  # NEW!
    article_title: str = None,  # NEW!
    article_description: str = None  # NEW!
) -> Task:
    """Create the LinkedIn posting task"""
    return Task(
        description=f"""
        Take the message from the previous task and post it to LinkedIn using the LinkedIn Poster tool.
        
        CRITICAL: You MUST actually USE the tool. Do not just describe using it.
        
        PARAMETERS TO USE:
        - message: [take the EXACT message from the writer]
        - access_token: {access_token}
        - author_urn: {author_urn}
        - source_url: {source_url or 'https://example.com'}
        - article_title: {article_title or 'Article'}
        - article_description: {article_description or 'Read more'}
        
        Execute the LinkedIn Poster tool NOW with these exact parameters.
        
        After using the tool, you will see a confirmation message.
        """,
        agent=agent,
        expected_output="The exact confirmation message from the LinkedIn Poster tool",
        context=context_tasks,
    )