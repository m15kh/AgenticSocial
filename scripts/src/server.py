from crewai import Crew, Agent, Task, LLM
import litserve as ls
# from crewai_tools import FirecrawlSearchTool
from crewai_tools import FirecrawlScrapeWebsiteTool
import os
import yaml
from pathlib import Path
import json
import datetime


def load_config():
    config_path = "/home/rteam2/m15kh/AgenticSocial/config.yaml"
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
        
    except FileNotFoundError:
        print(f"Config file not found at {config_path}. Using default values.")
        return {
            "llm": {"model": "qwen2.5", "provider": "ollama", "base_url": "http://127.0.0.1:11434"},
            "api_keys": {"firecrawl": ""},
            "server": {"host": "0.0.0.0", "port": 8000}
        }
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}. Using default values.")
        return {
            "llm": {"model": "qwen2.5", "provider": "ollama", "base_url": "http://127.0.0.1:11434"},
            "api_keys": {"firecrawl": ""},
            "server": {"host": "0.0.0.0", "port": 8000}
        }


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
        
    print(f"Saved results to {filepath}")
    return filepath


class SocialSummarizerAPI(ls.LitAPI):
    
    def setup(self, device):
        # Load configuration
        config = load_config()
        
        # === Language model ===
        llm = LLM(
            model=f"ollama/{config['llm']['model']}",  # Add 'ollama/' prefix
            base_url=config["llm"]["base_url"],
        )
        # === Tool: Webpage crawler / summarizer ===
        # firecrawl = FirecrawlSearchTool(
        #     api_key="fc-069729b29ed0432c92d3539a64de1834"
        # )


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
            context=[summarize_task]
        )

        self.crew = Crew(
            agents=[researcher, writer],
            tasks=[summarize_task, telegram_task],
            verbose=True,
        )

    def decode_request(self, request):
        return request["url"]

    def predict(self, url: str):
        # Process URL with CrewAI
        result = self.crew.kickoff(inputs={"url": url})
        
        # Format the output
        if isinstance(result, dict):
            output = {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": result.get("summary") or result.get("raw") or str(result),
                "tweet": result.get("tweet") or result.get("final_output") or str(result),
            }
        else:
            output = {
                "url": url, 
                "timestamp": datetime.datetime.now().isoformat(),
                "output": str(result)
            }
        
        # Save results to file
        saved_path = save_results(url, output)
        
        # Add save information to output
        output["saved_to"] = str(saved_path)
        
        return output

    def encode_response(self, output):
        return {"output": output, "status": "success"}


if __name__ == "__main__":
    config = load_config()
    print(f"Starting server on {config['server']['host']}:{config['server']['port']}")
    print("POST to /predict with JSON: {'url': 'https://aws.amazon.com/what-is/reinforcement-learning-from-human-feedback/'}")

    api = SocialSummarizerAPI()
    server = ls.LitServer(api)  # you can pass accelerator="cpu" or "gpu"
    server.run(
        host=config["server"]["host"],
        port=8080
    )
