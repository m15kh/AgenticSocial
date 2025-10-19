import litserve as ls
import datetime
from crewai import Crew, LLM

from scripts.src.config.loader import load_config
from scripts.src.utils.logger import setup_logger, log_info, log_success, log_warning
from scripts.src.utils.storage import save_results
from scripts.src.tools.web_scraper import WebScraperTool
from scripts.src.tools.telegram_poster import TelegramPosterTool
from scripts.src.agents.researcher import create_researcher
from scripts.src.agents.writer import create_writer
from scripts.src.agents.telegram_poster import create_telegram_poster
from scripts.src.tasks.summarize import create_summarize_task
from scripts.src.tasks.social import create_social_task
from scripts.src.tasks.telegram import create_telegram_task

from crewai import Agent, Task, Crew
from scripts.src.utils.link_analyzer import analyze_link
from scripts.src.utils.template_loader import template_loader
import re

# Add this import at the top
from fastapi import FastAPI
import litserve as ls


logger = setup_logger('API')


class SocialSummarizerAPI(ls.LitAPI):
        
    def setup(self, device):
        """Setup the API with agents and tasks"""
        # Load configuration
        self.config = load_config()
        log_info(logger, f"Setting up API with model: {self.config['llm']['model']}")
        
        # Initialize LLM
        self.llm = LLM(
            model=f"ollama/{self.config['llm']['model']}",
            base_url=self.config["llm"]["base_url"],
        )
        
        log_success(logger, "API setup completed successfully")

    def decode_request(self, request):
        """Decode incoming request"""
        return request["url"]
    
    def predict(self, url: str):
        """Process URL, generate content, and post to Telegram, Twitter, AND LinkedIn"""
        log_warning(logger, f"Processing URL: {url}")
        
        try:
            # Initialize tools
            from scripts.src.tools.web_scraper import WebScraperTool
            from scripts.src.tools.telegram_poster import TelegramPosterTool
            from scripts.src.tools.twitter_poster import TwitterPosterTool
            from scripts.src.tools.linkedin_poster import LinkedInPosterTool
            
            web_scraper = WebScraperTool()
            telegram_poster = TelegramPosterTool()
            twitter_poster = TwitterPosterTool()
            linkedin_poster = LinkedInPosterTool()
            
            # Create agents
            from scripts.src.agents.researcher import create_researcher
            from scripts.src.agents.writer import create_writer
            from scripts.src.agents.telegram_poster import create_telegram_poster
            from scripts.src.agents.twitter_poster import create_twitter_poster
            from scripts.src.agents.linkedin_poster import create_linkedin_poster
            
            researcher = create_researcher(self.llm, [web_scraper])
            telegram_writer = create_writer(self.llm)
            twitter_writer = create_writer(self.llm)
            linkedin_writer = create_writer(self.llm)
            telegram_agent = create_telegram_poster(self.llm, [telegram_poster])
            twitter_agent = create_twitter_poster(self.llm, [twitter_poster])
            linkedin_agent = create_linkedin_poster(self.llm, [linkedin_poster])
            
            # Get social links
            social_links = self.config.get('social', {})
            
            # Create tasks
            from scripts.src.tasks.summarize import create_summarize_task
            from scripts.src.tasks.social import create_social_task
            from scripts.src.tasks.telegram import create_telegram_task
            from scripts.src.tasks.twitter import create_twitter_task
            from scripts.src.tasks.linkedin import create_linkedin_task
            from scripts.src.utils.template_loader import template_loader
            from crewai import Task
            
            # 1. Summarize
            summarize_task = create_summarize_task(researcher, url)
            
            # 2. Write Telegram post
            telegram_social_task = create_social_task(
                telegram_writer, 
                [summarize_task], 
                source_url=url,
                social_links=social_links
            )
            
            # 3. Write Twitter post
            twitter_description = template_loader.load('twitter_writer', source_url=url)
            twitter_social_task = Task(
                description=twitter_description,
                agent=twitter_writer,
                expected_output="A concise Twitter post under 280 characters",
                context=[summarize_task]
            )
            
            # 4. Write LinkedIn post
            linkedin_description = template_loader.load('linkedin_writer', source_url=url)
            linkedin_social_task = Task(
                description=linkedin_description,
                agent=linkedin_writer,
                expected_output="A professional LinkedIn post with insights",
                context=[summarize_task]
            )
            
            # 5. Post to Telegram
            telegram_post_task = create_telegram_task(
                telegram_agent, 
                [telegram_social_task],
                self.config['telegram']['bot_token'],
                self.config['telegram']['channel_id']
            )
            
            # 6. Post to Twitter
            twitter_post_task = create_twitter_task(
                twitter_agent,
                [twitter_social_task],
                self.config['twitter']['api_key'],
                self.config['twitter']['api_secret'],
                self.config['twitter']['access_token'],
                self.config['twitter']['access_token_secret']
            )
            
            # 7. Post to LinkedIn
            linkedin_post_task = create_linkedin_task(
                linkedin_agent,
                [linkedin_social_task],
                self.config['linkedin']['access_token'],
                self.config['linkedin']['author_urn']
            )
            
            # Create crew with all agents
            crew = Crew(
                agents=[
                    researcher, 
                    telegram_writer, 
                    twitter_writer, 
                    linkedin_writer,
                    telegram_agent, 
                    twitter_agent,
                    linkedin_agent
                ],
                tasks=[
                    summarize_task, 
                    telegram_social_task, 
                    twitter_social_task,
                    linkedin_social_task,
                    telegram_post_task, 
                    twitter_post_task,
                    linkedin_post_task
                ],
                verbose=True,
            )
            
            log_info(logger, "Starting crew execution...")
            
            # Execute
            result = crew.kickoff(inputs={"url": url})
            
            # Format output
            output = {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "result": str(result),
                "status": "success",
                "posted_to": ["telegram", "twitter", "linkedin"]
            }
            
            # Save results
            saved_path = save_results(url, output)
            output["saved_to"] = str(saved_path)
            
            log_success(logger, f"Successfully posted to Telegram, Twitter, AND LinkedIn!")
            
            return output
            
        except Exception as e:
            log_error(logger, f"Error processing URL: {str(e)}")
            return {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    def encode_response(self, output):
        """Encode response for API"""
        return {
            "output": output, 
            "status": output.get("status", "success")
        }
        
        
class EnhancementAPI(ls.LitAPI):
    
    def setup(self, device):
        """Setup LLM for text enhancement"""
        self.config = load_config()
        
        if self.config['llm']['provider'] == 'openai':
            self.llm = LLM(
                model=self.config['llm']['model'],
                api_key=self.config['llm']['api_key']
            )
        else:
            self.llm = LLM(
                model=f"ollama/{self.config['llm']['model']}",
                base_url=self.config["llm"]["base_url"],
            )

    def decode_request(self, request):
        return request["text"]

    def predict(self, text: str):
        """Enhance user's text with AI"""

        # Find URLs and analyze
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        link_context = ""
        for url in urls:
            info = analyze_link(url, self.config.get('firecrawl', ''))
            if info.get('description'):
                link_context += f"\nLink: {url}\nTitle: {info['title']}\nDescription: {info['description']}\n"
        
        # Get social links
        social_links = self.config.get('social', {})
        
        # Create agent
        enhancer = Agent(
            role="Social Media Content Editor",
            goal="Transform rough text into engaging, polished social media posts",
            backstory="You're an expert social media editor.",
            llm=self.llm,
            verbose=False
        )
        
        # Load template with variables
        if link_context:
            link_section = f"ADDITIONAL CONTEXT ABOUT LINKS:\n{link_context}\n\nUse this information to write engaging descriptions."
        else:
            link_section = ""
        
        description = template_loader.load(
            'enhancer',
            user_text=text,
            link_context=link_section,
            twitter_url=social_links.get('twitter', ''),
            linkedin_url=social_links.get('linkedin', ''),
            youtube_url=social_links.get('youtube', ''),
            telegram_url=social_links.get('telegram_public', '')
        )
        
        # Create task
        task = Task(
            description=description,
            agent=enhancer,
            expected_output="Polished social media post"
        )
        
        # Run
        crew = Crew(agents=[enhancer], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        return {"enhanced_text": str(result)}

    def encode_response(self, output):
        return output