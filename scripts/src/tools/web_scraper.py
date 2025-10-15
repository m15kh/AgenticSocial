from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
from bs4 import BeautifulSoup

class WebScraperInput(BaseModel):
    """Input schema for WebScraperTool"""
    url: str = Field(..., description="Website URL to scrape")

class WebScraperTool(BaseTool):
    name: str = "Web Scraper"
    description: str = "Scrapes web pages and returns their text content"
    args_schema: Type[BaseModel] = WebScraperInput

    def _run(self, url: str) -> str:
        """Scrape a webpage and return its text content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to first 5000 chars
            
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"