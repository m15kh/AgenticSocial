from crewai import Task, Agent


def create_hashtag_task(agent: Agent, context_tasks: list, platform: str = "all") -> Task:
    """
    Create the hashtag generation task
    
    Args:
        agent: The hashtag generator agent
        context_tasks: Previous tasks (summary, written content)
        platform: Target platform (twitter, linkedin, telegram, or all)
    """
    
    platform_guidelines = {
        "twitter": "2-3 hashtags maximum, mix of popular and niche",
        "linkedin": "3-5 hashtags, professional and industry-specific",
        "telegram": "3-4 hashtags, community-focused",
        "all": "Generate separate hashtag sets for each platform"
    }
    
    guideline = platform_guidelines.get(platform, platform_guidelines["all"])
    
    return Task(
        description=f"""
        Analyze the content from previous tasks and generate relevant, effective hashtags.
        
        PLATFORM: {platform}
        GUIDELINE: {guideline}
        
        === YOUR EXPERTISE ===
        - Identify main topics, keywords, and themes
        - Consider current trends in AI/ML/Tech
        - Balance between reach (popular tags) and engagement (niche tags)
        - Use proper capitalization for readability (e.g., #MachineLearning not #machinelearning)
        
        === HASHTAG STRATEGY ===
        1. Primary hashtags (1-2): Main topic, high search volume
           Examples: #AI #MachineLearning #DeepLearning
        
        2. Secondary hashtags (1-2): More specific, medium search volume
           Examples: #NLP #ComputerVision #LLM
        
        3. Niche hashtags (0-1): Very specific, low competition
           Examples: #VisionLanguageModels #TransformerArchitecture
        
        === BEST PRACTICES ===
        ✅ Use CamelCase for multi-word hashtags: #ArtificialIntelligence
        ✅ Mix trending and evergreen hashtags
        ✅ Include relevant community hashtags: #100DaysOfCode #TechTwitter
        ✅ Keep hashtags relevant to the content
        
        ❌ Don't use too many hashtags (looks spammy)
        ❌ Don't use overly generic tags like #tech #news
        ❌ Don't use banned or controversial hashtags
        
        === OUTPUT FORMAT ===
        For Twitter: 2-3 hashtags
        For LinkedIn: 3-5 hashtags  
        For Telegram: 3-4 hashtags
        
        Return hashtags as a simple list, one per line:
        #HashtagOne
        #HashtagTwo
        #HashtagThree
        
        Also provide a brief explanation (1 sentence) of why you chose these hashtags.
        """,
        agent=agent,
        expected_output=f"A curated list of {guideline} with brief reasoning",
        context=context_tasks,
    )