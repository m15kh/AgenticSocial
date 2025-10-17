from crewai import Task, Agent


def create_social_task(agent: Agent, context_tasks: list, source_url: str, social_links: dict) -> Task:
    """Create the social media posting task"""
    
    # Build social media links section
    twitter_link = social_links.get('twitter', '')
    linkedin_link = social_links.get('linkedin', '')
    youtube_link = social_links.get('youtube', '')
    telegram_link = social_links.get('telegram_public', '')
    
    return Task(
        description=f"""
        Write a simple, conversational Telegram post based on the summary.
        
        === STYLE ===
        ✅ Simple, friendly language (like talking to a friend)
        ✅ Practical examples and resources
        ✅ Minimal emojis (1-2 max)
        
        === STRUCTURE ===
        1. Hook (interesting question/statement)
        2. Main explanation (2-3 simple sentences)
        3. Practical resources (GitHub, tutorials)
        4. Source article link
        5. Social media links section
        6. Hashtags (2-3)
        
        === FORMATTING ===
        Use HTML: <b>bold</b>, <i>italic</i>, <a href="URL">link</a>
        
        === EXAMPLE OUTPUT ===
        
        Want to understand how AI learns from feedback?
        
        <b>RLHF</b> (Reinforcement Learning from Human Feedback) is the technique. Train model → get human feedback → fine-tune. Simple but powerful.
        
        Try it: <a href="https://github.com/huggingface/trl">Hugging Face's TRL library</a>
        
        <a href="{source_url}">Read the full article</a>
        
        <b>Connect with us:</b>
        🐦 <a href="{twitter_link}">Twitter</a> | 💼 <a href="{linkedin_link}">LinkedIn</a> | 📺 <a href="{youtube_link}">YouTube</a> | 💬 <a href="{telegram_link}">Telegram</a>
        
        #AI #MachineLearning #RLHF
        
        ---
        
        CRITICAL:
        - Include ALL social media links in this format:
          🐦 <a href="{twitter_link}">Twitter</a> | 💼 <a href="{linkedin_link}">LinkedIn</a> | 📺 <a href="{youtube_link}">YouTube</a> | 💬 <a href="{telegram_link}">Telegram</a>
        - Use the EXACT URLs provided above
        - Keep it conversational
        """,
        agent=agent,
        expected_output="Simple post with article link and all social media links.",
        context=context_tasks,
    )