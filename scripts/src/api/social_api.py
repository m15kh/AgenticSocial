import litserve as ls
import datetime
from crewai import Crew, LLM
from colorama import init, Fore, Style

from scripts.src.config.loader import load_config
from scripts.src.utils.logger import setup_logger, setup_file_logger, log_info, log_success, log_warning, log_error
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


class SocialSummarizerAPI(ls.LitAPI):
        
    def setup(self, device):
        """Setup the API with agents and tasks"""
        # Load configuration
        self.config = load_config()
        
        # Setup logger with both console and file output
        self.logger = setup_logger('API')
        file_handler = setup_file_logger('social_api')
        self.logger.addHandler(file_handler)
        
        log_info(self.logger, f"Setting up API with model: {self.config['llm']['model']}")
        
        # Initialize LLM
        self.llm = LLM(
            model=f"ollama/{self.config['llm']['model']}",
            base_url=self.config["llm"]["base_url"],
        )
        
        log_success(self.logger, "API setup completed successfully")

    def decode_request(self, request):
        """Decode incoming request"""
        return request["url"]
            
    def predict(self, url: str):
        """Process URL, generate content with hashtags, and post to platforms"""
        log_warning(self.logger, f"Processing URL: {url}")
        
        try:
            # Initialize colorama
            init()

            # Read platform settings from config
            platforms = self.config.get('platforms', {})
            telegram_enabled = platforms.get('telegram', {}).get('enabled', True)
            twitter_enabled = platforms.get('twitter', {}).get('enabled', True)
            linkedin_enabled = platforms.get('linkedin', {}).get('enabled', True)
            
            # Print colorized platform status
            print("\n=== Platform Status ===")
            print(f"Telegram: {Fore.GREEN if telegram_enabled else Fore.RED}{'✓ Enabled' if telegram_enabled else '✗ Disabled'}{Style.RESET_ALL}")
            print(f"Twitter:  {Fore.GREEN if twitter_enabled else Fore.RED}{'✓ Enabled' if twitter_enabled else '✗ Disabled'}{Style.RESET_ALL}")
            print(f"LinkedIn: {Fore.GREEN if linkedin_enabled else Fore.RED}{'✓ Enabled' if linkedin_enabled else '✗ Disabled'}{Style.RESET_ALL}")
            print("==================\n")

            # Initialize tools
            from scripts.src.tools.web_scraper import WebScraperTool
            web_scraper = WebScraperTool()
            
            # Initialize researcher (always needed)
            from scripts.src.agents.researcher import create_researcher
            researcher = create_researcher(self.llm, [web_scraper])
            
            # Initialize hashtag agent (always needed)
            from scripts.src.agents.hashtag_generator import create_hashtag_generator
            from scripts.src.agents.writer import create_writer
            hashtag_agent = create_hashtag_generator(self.llm)
            
            social_links = self.config.get('social', {})
            
            # Create tasks
            from scripts.src.tasks.summarize import create_summarize_task
            from scripts.src.tasks.hashtag import create_hashtag_task
            from crewai import Task
            
            summarize_task = create_summarize_task(researcher, url)
            
            all_agents = [researcher, hashtag_agent]
            all_tasks = [summarize_task]
            posted_to = []
            
            # ===== TELEGRAM =====
            if telegram_enabled:
                from scripts.src.tools.telegram_poster import TelegramPosterTool
                from scripts.src.agents.telegram_poster import create_telegram_poster
                from scripts.src.tasks.social import create_social_task
                from scripts.src.tasks.telegram import create_telegram_task
                
                telegram_poster = TelegramPosterTool()
                telegram_writer = create_writer(self.llm)
                telegram_agent = create_telegram_poster(self.llm, [telegram_poster])
                
                telegram_hashtag_task = create_hashtag_task(
                    hashtag_agent, [summarize_task], platform="telegram"
                )
                
                telegram_social_task = create_social_task(
                    telegram_writer, 
                    [summarize_task, telegram_hashtag_task],
                    source_url=url,
                    social_links=social_links
                )
                
                telegram_post_task = create_telegram_task(
                    telegram_agent,
                    [telegram_social_task],
                    self.config['telegram']['bot_token'],
                    self.config['telegram']['channel_id']
                )
                
                all_agents.extend([telegram_writer, telegram_agent])
                all_tasks.extend([
                    telegram_hashtag_task,
                    telegram_social_task,
                    telegram_post_task
                ])
                posted_to.append("telegram")
            
            # ===== TWITTER =====
            if twitter_enabled:
                from scripts.src.tools.twitter_poster import TwitterPosterTool
                from scripts.src.agents.twitter_poster import create_twitter_poster
                from scripts.src.tasks.twitter import create_twitter_task
                from scripts.src.utils.template_loader import template_loader
                
                twitter_poster = TwitterPosterTool()
                twitter_writer = create_writer(self.llm)
                twitter_agent = create_twitter_poster(self.llm, [twitter_poster])
                
                twitter_hashtag_task = create_hashtag_task(
                    hashtag_agent, [summarize_task], platform="twitter"
                )
                
                twitter_description = template_loader.load('twitter_writer', source_url=url)
                twitter_social_task = Task(
                    description=twitter_description,
                    agent=twitter_writer,
                    expected_output="A concise Twitter post",
                    context=[summarize_task, twitter_hashtag_task]
                )
                
                twitter_post_task = create_twitter_task(
                    twitter_agent,
                    [twitter_social_task],
                    self.config['twitter']['api_key'],
                    self.config['twitter']['api_secret'],
                    self.config['twitter']['access_token'],
                    self.config['twitter']['access_token_secret']
                )
                
                all_agents.extend([twitter_writer, twitter_agent])
                all_tasks.extend([
                    twitter_hashtag_task,
                    twitter_social_task,
                    twitter_post_task
                ])
                posted_to.append("twitter")
            
            # ===== LINKEDIN =====
            if linkedin_enabled:
                from scripts.src.tools.linkedin_poster import LinkedInPosterTool
                from scripts.src.agents.linkedin_poster import create_linkedin_poster
                from scripts.src.tasks.linkedin import create_linkedin_task
                from scripts.src.utils.template_loader import template_loader
                
                linkedin_poster = LinkedInPosterTool()
                linkedin_writer = create_writer(self.llm)
                linkedin_agent = create_linkedin_poster(self.llm, [linkedin_poster])
                
                linkedin_hashtag_task = create_hashtag_task(
                    hashtag_agent, [summarize_task], platform="linkedin"
                )
                
                linkedin_description = template_loader.load('linkedin_writer', source_url=url)
                linkedin_social_task = Task(
                    description=linkedin_description,
                    agent=linkedin_writer,
                    expected_output="A professional LinkedIn post",
                    context=[summarize_task, linkedin_hashtag_task]
                )
                
                # Extract article info from URL
                import urllib.parse
                parsed_url = urllib.parse.urlparse(url)
                article_title = parsed_url.path.split('/')[-1].replace('-', ' ').title()
                article_description = f"Interesting article from {parsed_url.netloc}"
                
                linkedin_post_task = create_linkedin_task(
                    linkedin_agent,
                    [linkedin_social_task],
                    self.config['linkedin']['access_token'],
                    self.config['linkedin']['author_urn'],
                    source_url=url,
                    article_title=article_title,
                    article_description=article_description
                )
                
                all_agents.extend([linkedin_writer, linkedin_agent])
                all_tasks.extend([
                    linkedin_hashtag_task,
                    linkedin_social_task,
                    linkedin_post_task
                ])
                posted_to.append("linkedin")
            
            # Create crew with enabled platforms only
            crew = Crew(
                agents=all_agents,
                tasks=all_tasks,
                verbose=True,
            )
            
            log_info(self.logger, f"Starting crew execution for: {', '.join(posted_to)}...")
            
            result = crew.kickoff(inputs={"url": url})
            
            output = {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "result": str(result),
                "status": "success",
                "posted_to": posted_to
            }
            
            saved_path = save_results(url, output)
            output["saved_to"] = str(saved_path)
            
            log_success(self.logger, f"Successfully posted to: {', '.join(posted_to)}!")
            
            return output
            
        except Exception as e:
            log_error(self.logger, f"Error processing URL: {str(e)}")
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
        # Setup logger with both console and file output
        self.logger = setup_logger('EnhancementAPI')
        file_handler = setup_file_logger('enhancement_api')
        self.logger.addHandler(file_handler)
        
        self.config = load_config()
        log_info(self.logger, "Setting up Enhancement API")
        
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
        log_info(self.logger, "Processing text enhancement request")

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