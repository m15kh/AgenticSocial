from crewai import Task, Agent


def create_linkedin_task(agent: Agent, context_tasks: list, 
                        access_token: str, author_urn: str) -> Task:
    """Create the LinkedIn posting task"""
    return Task(
        description=f"""
        Take the message from the previous task and post it to LinkedIn using the LinkedIn Poster tool.
        
        CRITICAL: You MUST actually USE the tool. Do not just describe using it.
        
        NOTE: LinkedIn prefers professional, well-formatted content.
        
        Execute this action NOW:
        
        Tool: LinkedIn Poster
        Parameters:
        - message: [take the message from the writer]
        - access_token: {access_token}
        - author_urn: {author_urn}
        
        After using the tool, you will see a confirmation like:
        "✅ Successfully posted to LinkedIn! Post ID: [id]"
        
        That post ID is proof it worked.
        """,
        agent=agent,
        expected_output="The exact confirmation message from the LinkedIn Poster tool with post ID",
        context=context_tasks,
    )