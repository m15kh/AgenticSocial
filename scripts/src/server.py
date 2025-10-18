import sys
from pathlib import Path

# Add scripts/src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

import litserve as ls
from config.loader import load_config
from utils.logger import setup_logger, log_success, log_info
from api.social_api import SocialSummarizerAPI, EnhancementAPI

logger = setup_logger('Server')

def main():
    """Start the LitServe server with both APIs"""
    config = load_config()
    
    log_success(logger, f"Starting server on {config['server']['host']}:{config['server']['port']}")
    
    # Create both APIs
    social_api = SocialSummarizerAPI()
    enhance_api = EnhancementAPI()
    
    # Create servers
    server1 = ls.LitServer(social_api, api_path="/predict")
    server2 = ls.LitServer(enhance_api, api_path="/enhance")
    
    # Run on same port
    server1.run(
        host=config['server']['host'],
        port=config['server']['port']
    )

if __name__ == "__main__":
    main()