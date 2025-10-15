import logging
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def setup_logger(name='AgenticSocial'):
    """Configure and return a logger with colorized output"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

def log_info(logger, message):
    """Log info message with color"""
    logger.info(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

def log_success(logger, message):
    """Log success message with color"""
    logger.info(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def log_warning(logger, message):
    """Log warning message with color"""
    logger.warning(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def log_error(logger, message):
    """Log error message with color"""
    logger.error(f"{Fore.RED}{message}{Style.RESET_ALL}")