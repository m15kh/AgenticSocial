import sys
import os

# Add the project root directory to Python's path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.src.bot.telegram_bot import ContentBot

if __name__ == "__main__":
    bot = ContentBot()
    bot.run()
