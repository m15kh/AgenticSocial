from crewai import Crew, Agent, Task, LLM
import litserve as ls
# from crewai_tools import FirecrawlSearchTool
from crewai_tools import FirecrawlScrapeWebsiteTool
import os
import yaml
from pathlib import Path
import json
import datetime
import logging
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configure logger
def setup_logger():
    logger = logging.getLogger('AgenticSocial')
    logger.setLevel(logging.INFO)
    
    # Create console handler with colorized output
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()


def load_config():
    config_path = "/home/rteam2/m15kh/AgenticSocial/config.yaml"
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {config_path}. Please create a config file.")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing config file: {e}.")


def save_results(url, data):
    """Save the result to a JSON file"""
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parents[3] / "AgenticSocial" / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create a filename based on the URL (sanitized) and timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Remove protocol and replace special characters
    sanitized_url = url.replace("http://", "").replace("https://", "").replace("/", "_")
    sanitized_url = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in sanitized_url)
    
    # Truncate if too long
    if len(sanitized_url) > 50:
        sanitized_url = sanitized_url[:50]
    
    filename = f"{timestamp}_{sanitized_url}.json"
    filepath = data_dir / filename
    
    # Save the data to the file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"{Fore.GREEN}Saved results to {filepath}{Style.RESET_ALL}")
    return filepath


class SocialSummarizerAPI(ls.LitAPI):
    
    def setup(self, device):
        # Load configuration
        
        config = load_config()
        logger.info(f"{Fore.BLUE}Setting up API with model: {config['llm']['model']}{Style.RESET_ALL}")
        
        # === Language model ===
        llm = LLM(
            model=f"ollama/{config['llm']['model']}",  # Add 'ollama/' prefix
            base_url=config["llm"]["base_url"],
        )

        firecrawl = FirecrawlScrapeWebsiteTool(
            api_key=config["firecrawl"]
        )

        # === Agent 1: Summarizer ===
        researcher = Agent(
            role="Web Researcher",
            goal="Summarize the content of a given website link.",
            backstory="You are an expert at extracting the key insights from any article or webpage.",
            tools=[firecrawl],
            llm=llm,
            verbose=True,
        )

        summarize_task = Task(
            description="Fetch and summarize the webpage at: {url}",
            agent=researcher,
            expected_output="A clear, concise summary in 3 paragraphs.",  # Specify expected output format
            output_file="researcher_output.txt"  # Save researcher output to file
        )
        # === Agent 2: Social writer ===
        writer = Agent(
            role="Social-Media Writer",
            goal="Craft short, engaging tweets from summaries.",
            backstory="You are a creative writer skilled at making short, viral posts.",
            llm=llm,
            verbose=True,
        )

        telegram_task = Task(
            description="Write a single message (max 4096 chars) suitable for posting in a Telegram channel, summarizing this:",
            agent=writer,
            expected_output="One engaging Telegram channel message, concise and informative.",
            context=[summarize_task],
            output_file="writer_output.txt"  # Save writer output to file
        )

        self.crew = Crew(
            agents=[researcher, writer],
            tasks=[summarize_task, telegram_task],
            verbose=True,
        )

    def decode_request(self, request):
        return request["url"]

    def predict(self, url: str):
        logger.info(f"{Fore.YELLOW}Processing URL: {url}{Style.RESET_ALL}")
        
        # Process URL with CrewAI
        result = self.crew.kickoff(inputs={"url": url})
        
        # Capture agent outputs from the task files if they exist
        researcher_output = ""
        writer_output = ""
        
        try:
            if os.path.exists("researcher_output.txt"):
                with open("researcher_output.txt", "r") as f:
                    researcher_output = f.read()
                logger.info(f"{Fore.CYAN}Captured researcher output{Style.RESET_ALL}")
                
            if os.path.exists("writer_output.txt"):
                with open("writer_output.txt", "r") as f:
                    writer_output = f.read()
                logger.info(f"{Fore.CYAN}Captured writer output{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}Error reading output files: {str(e)}{Style.RESET_ALL}")
        
        # Format the output
        if isinstance(result, dict):
            output = {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": result.get("summary") or result.get("raw") or str(result),
                "tweet": result.get("tweet") or result.get("final_output") or str(result),
                "researcher_output": researcher_output,
                "writer_output": writer_output
            }
            logger.info(f"{Fore.GREEN}Successfully processed URL with structured output{Style.RESET_ALL}")
        else:
            output = {
                "url": url, 
                "timestamp": datetime.datetime.now().isoformat(),
                "output": str(result),
                "researcher_output": researcher_output,
                "writer_output": writer_output
            }
            logger.info(f"{Fore.YELLOW}Processed URL with unstructured output{Style.RESET_ALL}")
        
        # Save results to file
        saved_path = save_results(url, output)
        
        # Add save information to output
        output["saved_to"] = str(saved_path)
        
        # Clean up temporary files
        for file_path in ["researcher_output.txt", "writer_output.txt"]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"{Fore.RED}Error removing file {file_path}: {str(e)}{Style.RESET_ALL}")
        
        return output

    def encode_response(self, output):
        return {"output": output, "status": "success"}


if __name__ == "__main__":
    config = load_config()
    logger.info(f"{Fore.GREEN}Starting server on {config['server']['host']}:{config['server']['port']}{Style.RESET_ALL}")
    logger.info(f"{Fore.BLUE}POST to /predict with JSON: {{'url': 'https://aws.amazon.com/what-is/reinforcement-learning-from-human-feedback/'}}{Style.RESET_ALL}")

    api = SocialSummarizerAPI()
    server = ls.LitServer(api)  # you can pass accelerator="cpu" or "gpu"
    server.run(
        host=config["server"]["host"],
        port=8080
    )
