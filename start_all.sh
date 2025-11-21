#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🚀 Starting Social Media Bot Services"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu7/m15kh/own/AgenticSocial"
cd $PROJECT_DIR

# Activate conda environment (miniconda3)
echo "🐍 Activating conda environment 'mc'..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate mc

# Verify environment
echo "   Environment: mc"
echo "   Python: $(which python3)"
echo ""

# Create logs directory
mkdir -p logs
mkdir -p data

# Function to check if port is in use
check_port() {
    if lsof -i:$1 > /dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

# Kill existing processes
echo "🔄 Stopping any existing services..."
pkill -f "server_queued.py" 2>/dev/null
pkill -f "run_bot.py" 2>/dev/null
pkill -f "processor.py" 2>/dev/null
sleep 2

# Start API Server (Queued Mode)
echo ""
echo -e "${GREEN}1. Starting API Server (Queued Mode)...${NC}"
python3 scripts/src/server_queued.py > logs/server.log 2>&1 &
SERVER_PID=$!
echo "   PID: $SERVER_PID"
sleep 3

# Check if server started
if check_port 8080; then
    echo -e "   ${GREEN}✅ API Server running on port 8080${NC}"
else
    echo -e "   ${RED}❌ API Server failed to start${NC}"
    echo -e "   ${YELLOW}   Check logs/server.log for details${NC}"
fi

# Start Telegram Bot
echo ""
echo -e "${GREEN}2. Starting Telegram Bot...${NC}"
python3 scripts/src/run_bot.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "   PID: $BOT_PID"
sleep 2
echo -e "   ${GREEN}✅ Telegram Bot started${NC}"

# Start Queue Scheduler
echo ""
echo -e "${GREEN}3. Starting Queue Scheduler (processes at 23:00)...${NC}"
python3 scripts/src/scheduler/processor.py > logs/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "   PID: $SCHEDULER_PID"
sleep 2
echo -e "   ${GREEN}✅ Scheduler started${NC}"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ All services started!${NC}"
echo "=========================================="
echo ""
echo "📋 Service PIDs:"
echo "   API Server:   $SERVER_PID"
echo "   Telegram Bot: $BOT_PID"
echo "   Scheduler:    $SCHEDULER_PID"
echo ""
echo "📁 Log files:"
echo "   logs/server.log"
echo "   logs/bot.log"
echo "   logs/scheduler.log"
echo ""
echo "🔧 Commands:"
echo "   View queue:     curl http://localhost:8080/queue"
echo "   Process now:    python3 scripts/src/scheduler/processor.py --now"
echo "   Stop all:       pkill -f 'server_queued\|run_bot\|processor'"
echo ""
echo "=========================================="

# Keep script running to show logs
echo ""
echo "📺 Showing combined logs (Ctrl+C to exit)..."
echo ""
tail -f logs/server.log logs/bot.log logs/scheduler.log