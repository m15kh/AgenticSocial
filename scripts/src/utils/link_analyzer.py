from firecrawl import FirecrawlApp
import re


def analyze_link(url: str, api_key: str) -> dict:
    """
    Analyze a URL using Firecrawl to extract key information
    
    Args:
        url: The URL to analyze
        api_key: Firecrawl API key
    
    Returns:
        dict with title, description, and other metadata
    """
    try:
        # Initialize Firecrawl
        app = FirecrawlApp(api_key=api_key)
        
        # Scrape the URL
        result = app.scrape_url(url, params={
            'formats': ['markdown', 'html'],
        })
        
        # Extract content
        markdown_content = result.get('markdown', '')
        metadata = result.get('metadata', {})
        
        # Get title
        title = metadata.get('title', '') or metadata.get('ogTitle', '') or 'Link'
        
        # Get description
        description = metadata.get('description', '') or metadata.get('ogDescription', '')
        
        # If no description, extract first paragraph from markdown
        if not description and markdown_content:
            # Get first 2-3 sentences
            sentences = re.split(r'[.!?]\s+', markdown_content)
            description = '. '.join(sentences[:2]) + '.'
            # Limit length
            if len(description) > 300:
                description = description[:297] + '...'
        
        # Detect link type
        link_type = 'article'
        if 'amazon.com' in url:
            link_type = 'book'
        elif 'github.com' in url:
            link_type = 'github'
        elif 'youtube.com' in url or 'youtu.be' in url:
            link_type = 'video'
        
        return {
            'type': link_type,
            'title': title,
            'description': description,
            'url': url,
            'success': True
        }
        
    except Exception as e:
        print(f"Error analyzing link {url}: {str(e)}")
        # Return minimal info if Firecrawl fails
        return {
            'type': 'unknown',
            'title': url,
            'description': '',
            'url': url,
            'success': False
        }


def get_link_summary(url: str, api_key: str) -> str:
    """
    Get a human-readable summary of a link
    
    Returns a formatted string suitable for displaying to users
    """
    info = analyze_link(url, api_key)
    
    if not info['success']:
        return f"Link: {url}"
    
    summary = f"{info['type'].title()}: {info['title']}"
    if info['description']:
        summary += f"\n{info['description']}"
    
    return summary
