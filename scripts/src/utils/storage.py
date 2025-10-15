import json
import datetime
from pathlib import Path
from scripts.src.utils.logger import setup_logger, log_success

# ... rest of code

logger = setup_logger('Storage')

def save_results(url: str, data: dict) -> Path:
    """Save API results to JSON file"""
    # Create data directory
    data_dir = Path(__file__).parents[3] / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_url = sanitize_url(url)
    filename = f"{timestamp}_{sanitized_url}.json"
    filepath = data_dir / filename
    
    # Save data
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_success(logger, f"Saved results to {filepath}")
    return filepath

def sanitize_url(url: str) -> str:
    """Sanitize URL for use in filename"""
    sanitized = url.replace("http://", "").replace("https://", "")
    sanitized = sanitized.replace("/", "_")
    sanitized = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in sanitized)
    
    # Truncate if too long
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    return sanitized