#!/usr/bin/env python3
"""
Simple bot starter - run from anywhere
"""
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

print("=" * 60)
print("🤖 Starting Telegram Social Media Bot")
print("=" * 60)
print(f"📁 Project root: {project_root}")
print("💡 Make sure API server is running on http://localhost:8080")
print("\n⚠️  Press Ctrl+C to stop\n")
print("=" * 60)
print()

if __name__ == '__main__':
    from scripts.src.bot.telegram_bot import main
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")