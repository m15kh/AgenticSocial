import re
from urllib.parse import urlparse


def extract_article_info(url: str, summary: str = None) -> dict:
    """
    Extract article title and description from URL and optional summary
    
    Args:
        url: Source URL of the article
        summary: Optional summary text to extract title from
    
    Returns:
        dict with 'title', 'description', and 'domain'
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    # Try to get title from URL path
    path_parts = parsed.path.strip('/').split('/')
    url_title = path_parts[-1] if path_parts else 'article'
    url_title = url_title.replace('-', ' ').replace('_', ' ').title()
    
    # If summary provided, try to extract title from first line
    title = url_title
    description = f"Article from {domain}"
    
    if summary:
        lines = summary.strip().split('\n')
        if lines:
            # First non-empty line is often the title
            first_line = lines[0].strip()
            if first_line and len(first_line) < 100:
                title = first_line
            
            # Use second paragraph as description
            if len(lines) > 1:
                desc_lines = [l.strip() for l in lines[1:3] if l.strip()]
                if desc_lines:
                    description = ' '.join(desc_lines)[:200]  # Max 200 chars
    
    return {
        'title': title,
        'description': description,
        'domain': domain
    }


# Example usage
if __name__ == "__main__":
    url = "https://huggingface.co/blog/vlms-2025"
    summary = """
    Vision Language Models in 2025
    
    Vision Language Models are revolutionizing AI by combining visual and textual understanding.
    These models can process images and text simultaneously, enabling new applications.
    """
    
    info = extract_article_info(url, summary)
    print(f"Title: {info['title']}")
    print(f"Description: {info['description']}")
    print(f"Domain: {info['domain']}")