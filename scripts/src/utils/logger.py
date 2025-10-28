import logging
from colorama import Fore, Style, init
from logging.handlers import RotatingFileHandler
import os

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

def setup_file_logger(name, log_dir='logs'):
    """Setup a file logger that writes to a text file"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create file handler
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    
    # Set format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    return file_handler

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