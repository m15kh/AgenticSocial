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
        """Process URL, generate content, and post to Telegram"""
        log_warning(logger, f"Processing URL: {url}")
        
        try:
            # Initialize tools
            web_scraper = WebScraperTool()
            telegram_poster = TelegramPosterTool()
            
            # Create agents
            researcher = create_researcher(self.llm, [web_scraper])
            writer = create_writer(self.llm)
            telegram_agent = create_telegram_poster(self.llm, [telegram_poster])
            
            # Get social links from config
            social_links = self.config.get('social', {})
            
            # Create tasks
            summarize_task = create_summarize_task(researcher)
            
            social_task = create_social_task(
                writer, 
                [summarize_task], 
                source_url=url,
                social_links=social_links  # Pass all social links
            )
            
            telegram_task = create_telegram_task(
                telegram_agent, 
                [social_task],
                self.config['telegram']['bot_token'],
                self.config['telegram']['channel_id']
            )
            
            # Create crew
            crew = Crew(
                agents=[researcher, writer, telegram_agent],
                tasks=[summarize_task, social_task, telegram_task],
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
                "status": "success"
            }
            
            # Save results
            saved_path = save_results(url, output)
            output["saved_to"] = str(saved_path)
            
            log_success(logger, f"Successfully processed URL and posted to Telegram!")
            
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