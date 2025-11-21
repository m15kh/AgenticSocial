import schedule
import time
import logging
from datetime import datetime
import sys
import os
from colorama import init, Fore, Style
import warnings

# Initialize colorama
init(autoreset=True)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from scripts.src.utils.queue_manager import (
    get_pending_requests, 
    mark_as_processed, 
    remove_processed
)
from scripts.src.config.loader import load_config

# Suppress warnings
warnings.filterwarnings('ignore')

# Suppress verbose logging from other libraries
logging.getLogger('LiteLLM').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('crewai').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

# Custom colored logging formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)


# Setup logging with colors
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Apply colored formatter
for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))

config = load_config()
SCHEDULED_TIME = config.get('scheduler', {}).get('time', '23:00')


def print_header(text):
    """Print a colorized header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text:^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}\n")


def print_section(emoji, text, color=Fore.BLUE):
    """Print a colorized section"""
    print(f"{color}{Style.BRIGHT}{emoji} {text}{Style.RESET_ALL}")


def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}{Style.BRIGHT}✅ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}{Style.BRIGHT}❌ {text}{Style.RESET_ALL}")


def print_info(text):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")


def process_single_request(request_data):
    """Process a single request directly (not via API)"""
    
    try:
        # Suppress all output from CrewAI and LLM
        import sys
        from io import StringIO
        
        # Save original stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        # Redirect to null
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            # Check request type
            if "url" in request_data:
                from scripts.src.api.social_api import SocialSummarizerAPI
                
                api = SocialSummarizerAPI()
                api.setup(device=None)
                result = api.predict(request_data)
                
            elif "text" in request_data:
                from scripts.src.api.social_api import EnhancementAPI
                
                api = EnhancementAPI()
                api.setup(device=None)
                result = api.predict(request_data)
            else:
                result = {"status": "failed", "error": "Unknown request type"}
                
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        return result
            
    except Exception as e:
        # Restore stdout/stderr in case of error
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        logger.error(f"Error processing request: {e}")
        return {"status": "failed", "error": str(e)}


def process_all_queue():
    """Process ALL pending requests in queue"""
    
    print_header("🕐 QUEUE PROCESSING STARTED")
    print(f"{Fore.CYAN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}\n")
    
    pending = get_pending_requests()
    
    if not pending:
        print_info("No pending requests in queue")
        return {
            "status": "success",
            "processed": 0,
            "failed": 0,
            "message": "No requests to process"
        }
    
    print_section("📬", f"Found {len(pending)} pending request(s)", Fore.BLUE)
    print_section("📤", "Processing ALL requests...", Fore.MAGENTA)
    print()
    
    processed_count = 0
    failed_count = 0
    
    for i, item in enumerate(pending, 1):
        request_id = item.get("id")
        request_data = item.get("data", {})
        
        # Print minimal request header
        print(f"\n{Fore.YELLOW}{'─'*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}📋 Request {i}/{len(pending)} (ID: {request_id}){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'─'*60}{Style.RESET_ALL}")
        
        # Print compact request details
        if "url" in request_data:
            url = request_data['url']
            url_short = url if len(url) < 70 else url[:67] + "..."
            print(f"{Fore.CYAN}🔗 {url_short}{Style.RESET_ALL}")
        elif "text" in request_data:
            text_preview = request_data['text'][:50] + "..." if len(request_data['text']) > 50 else request_data['text']
            print(f"{Fore.CYAN}📝 {text_preview}{Style.RESET_ALL}")
        
        platforms = request_data.get('platforms', {})
        enabled = [k for k, v in platforms.items() if v]
        if enabled:
            platform_emoji = {'telegram': '🔵', 'twitter': '🐦', 'linkedin': '💼'}
            platform_str = ' '.join([f"{platform_emoji.get(p, '📤')} {p}" for p in enabled])
            print(f"{Fore.CYAN}{platform_str}{Style.RESET_ALL}")
        print()
        
        # Show loading animation
        import itertools
        import threading
        
        loading = True
        def animate():
            for c in itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']):
                if not loading:
                    break
                print(f'\r{Fore.YELLOW}   {c} Processing...{Style.RESET_ALL}', end='', flush=True)
                time.sleep(0.1)
        
        t = threading.Thread(target=animate)
        t.daemon = True
        t.start()
        
        try:
            # Process the request
            result = process_single_request(request_data)
            
            loading = False
            t.join(timeout=0.5)
            print('\r' + ' ' * 50 + '\r', end='')  # Clear loading line
            
            if result.get("status") == "success":
                posted_to = result.get('posted_to', [])
                print_success(f"Processed successfully")
                if posted_to:
                    posted_str = ', '.join(posted_to)
                    print(f"{Fore.GREEN}   📤 Posted to: {posted_str}{Style.RESET_ALL}")
                mark_as_processed(request_id)
                processed_count += 1
            else:
                error_msg = result.get('error', 'Unknown error')
                error_short = error_msg[:80] + "..." if len(error_msg) > 80 else error_msg
                print_error(f"Failed: {error_short}")
                failed_count += 1
                
        except Exception as e:
            loading = False
            t.join(timeout=0.5)
            print('\r' + ' ' * 50 + '\r', end='')
            print_error(f"Error: {str(e)}")
            failed_count += 1
        
        # Progress indicator
        progress = (i / len(pending)) * 100
        progress_bar = '█' * int(progress / 5) + '░' * (20 - int(progress / 5))
        print(f"\n{Fore.CYAN}Progress: [{progress_bar}] {progress:.0f}%{Style.RESET_ALL}")
        
        # Small delay between requests
        if i < len(pending):
            time.sleep(2)
    
    # Clean up processed requests
    remove_processed()
    
    # Print summary
    print_header("✅ QUEUE PROCESSING COMPLETED")
    
    print(f"{Fore.BLUE}{Style.BRIGHT}📊 Summary:{Style.RESET_ALL}")
    print(f"   {Fore.CYAN}Total: {len(pending)}{Style.RESET_ALL}")
    print(f"   {Fore.GREEN}✅ Success: {processed_count}{Style.RESET_ALL}")
    print(f"   {Fore.RED}❌ Failed: {failed_count}{Style.RESET_ALL}")
    print()
    
    return {
        "status": "success",
        "processed": processed_count,
        "failed": failed_count,
        "total": len(pending),
        "message": f"Processed {processed_count} requests, {failed_count} failed"
    }


def run_scheduler():
    """Run the scheduler that processes ALL queue at scheduled time"""
    
    print_header("🕐 QUEUE SCHEDULER")
    
    print(f"{Fore.BLUE}{Style.BRIGHT}Configuration:{Style.RESET_ALL}")
    print(f"   📅 Scheduled time: {Fore.CYAN}{SCHEDULED_TIME}{Style.RESET_ALL} (daily)")
    print(f"   📊 Mode: {Fore.CYAN}Process ALL queued requests{Style.RESET_ALL}")
    print(f"   ⏳ Status: {Fore.GREEN}Waiting for scheduled time...{Style.RESET_ALL}")
    print()
    
    # Schedule the job to process ALL queue at scheduled time
    schedule.every().day.at(SCHEDULED_TIME).do(process_all_queue)
    
    print(f"{Fore.YELLOW}{Style.BRIGHT}💡 Tips:{Style.RESET_ALL}")
    print(f"   • Process all now:  {Fore.CYAN}python3 scripts/src/scheduler/processor.py --now{Style.RESET_ALL}")
    print(f"   • Or use Telegram:  {Fore.CYAN}/processall{Style.RESET_ALL} command")
    print(f"   • Change time:      {Fore.CYAN}Edit config.yaml → scheduler.time{Style.RESET_ALL}")
    print()
    
    print(f"{Fore.GREEN}{Style.BRIGHT}✅ Scheduler is running! Press Ctrl+C to stop.{Style.RESET_ALL}\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Queue Processor - Process ALL queue daily')
    parser.add_argument('--now', action='store_true', help='Process ALL requests immediately')
    args = parser.parse_args()
    
    if args.now:
        print_section("🚀", "Processing ALL requests immediately (manual trigger)", Fore.MAGENTA)
        process_all_queue()
    else:
        run_scheduler()