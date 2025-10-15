import litserve as ls
from scripts.src.config.loader import load_config
from scripts.src.utils.logger import setup_logger, log_success, log_info
from scripts.src.api.social_api import SocialSummarizerAPI

logger = setup_logger('Server')

def main():
    """Start the LitServe server"""
    config = load_config()
    
    log_success(logger, f"Starting server on {config['server']['host']}:{config['server']['port']}")
    log_info(logger, "POST to /predict with JSON: {'url': 'https://example.com'}")
    
    api = SocialSummarizerAPI()
    server = ls.LitServer(api)
    
    server.run(
        host=config['server']['host'],
        port=config['server']['port']
    )

if __name__ == "__main__":
    main()