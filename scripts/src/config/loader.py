import yaml
from pathlib import Path

def load_config(config_path: str = None):
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parents[3] / "config.yaml"
        print(f"Config path: {config_path}")
    
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {config_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing config file: {e}")