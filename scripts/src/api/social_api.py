import litserve as ls
import datetime
from crewai import Crew, LLM

from scripts.src.config.loader import load_config
from scripts.src.utils.logger import setup_logger, log_info, log_success, log_warning
from scripts.src.utils.storage import save_results
from scripts.src.tools.web_scraper import WebScraperTool
from scripts.src.agents.researcher import create_researcher
from scripts.src.agents.writer import create_writer
from scripts.src.tasks.summarize import create_summarize_task
from scripts.src.tasks.social import create_social_task

# ... rest of code
logger = setup_logger('API')

class SocialSummarizerAPI(ls.LitAPI):
    
    def setup(self, device):
        """Setup the API with agents and tasks"""
        config = load_config()
        log_info(logger, f"Setting up API with model: {config['llm']['model']}")
        
        # Initialize LLM
        llm = LLM(
            model=f"ollama/{config['llm']['model']}",
            base_url=config["llm"]["base_url"],
        )
        
        # Initialize tools
        web_scraper = WebScraperTool()
        
        # Create agents
        researcher = create_researcher(llm, [web_scraper])
        writer = create_writer(llm)
        
        # Create tasks
        summarize_task = create_summarize_task(researcher)
        social_task = create_social_task(writer, [summarize_task])
        
        # Create crew
        self.crew = Crew(
            agents=[researcher, writer],
            tasks=[summarize_task, social_task],
            verbose=True,
        )

    def decode_request(self, request):
        """Decode incoming request"""
        return request["url"]

    def predict(self, url: str):
        """Process URL and generate social media content"""
        log_warning(logger, f"Processing URL: {url}")
        
        # Process with CrewAI
        result = self.crew.kickoff(inputs={"url": url})
        
        # Format output
        output = {
            "url": url,
            "timestamp": datetime.datetime.now().isoformat(),
            "result": str(result)
        }
        
        # Save results
        saved_path = save_results(url, output)
        output["saved_to"] = str(saved_path)
        
        log_success(logger, "Successfully processed URL")
        return output

    def encode_response(self, output):
        """Encode response"""
        return {"output": output, "status": "success"}