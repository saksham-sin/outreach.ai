#!/bin/bash
# Outreach.AI Startup Script (Unix/Linux/macOS)
# This script starts all components of the application in separate terminals

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================${NC}"
echo -e "${CYAN}   Outreach.AI Application Starter  ${NC}"
echo -e "${CYAN}====================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}ERROR: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}ERROR: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if Python virtual environment exists
VENV_DIR="$BACKEND_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}ERROR: Python virtual environment not found at $VENV_DIR${NC}"
    echo -e "${YELLOW}Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if node_modules exists
NODE_MODULES="$FRONTEND_DIR/node_modules"
if [ ! -d "$NODE_MODULES" ]; then
    echo -e "${YELLOW}WARNING: node_modules not found. Installing frontend dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    cd "$SCRIPT_DIR"
fi

# Check if backend .env exists
BACKEND_ENV="$BACKEND_DIR/.env"
if [ ! -f "$BACKEND_ENV" ]; then
    echo -e "${YELLOW}WARNING: Backend .env file not found at $BACKEND_ENV${NC}"
    echo -e "${YELLOW}Please create a .env file with required configuration${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Starting application components...${NC}"
echo ""

# Function to open a new terminal window based on OS
open_terminal() {
    local title=$1
    local command=$2
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell application \"Terminal\" to do script \"printf '\\\\e]2;$title\\\\a' && $command\""
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - try different terminal emulators
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal --title="$title" -- bash -c "$command; exec bash"
        elif command -v konsole &> /dev/null; then
            konsole --title "$title" -e bash -c "$command; exec bash" &
        elif command -v xterm &> /dev/null; then
            xterm -T "$title" -e bash -c "$command; exec bash" &
        else
            echo -e "${RED}No supported terminal emulator found${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
        exit 1
    fi
}

# Store PIDs for cleanup
PIDS=()

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    for pid in "${PIDS[@]}"; do
        kill -TERM "$pid" 2>/dev/null || true
    done
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start Backend API Server
echo -e "${YELLOW}[1/3] Starting Backend API Server...${NC}"
BACKEND_CMD="cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}Backend API Server Starting...${NC}' && echo -e '${CYAN}API will be available at: http://localhost:8000${NC}' && echo -e '${CYAN}API Docs available at: http://localhost:8000/docs${NC}' && echo '' && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
open_terminal "Backend API" "$BACKEND_CMD"
sleep 2

# Start Background Worker
echo -e "${YELLOW}[2/3] Starting Background Worker...${NC}"
WORKER_CMD="cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}Background Worker Starting...${NC}' && echo -e '${CYAN}Processing scheduled email jobs...${NC}' && echo '' && python -m app.services.worker"
open_terminal "Background Worker" "$WORKER_CMD"
sleep 2

# Start Frontend Development Server
echo -e "${YELLOW}[3/3] Starting Frontend Development Server...${NC}"
FRONTEND_CMD="cd '$FRONTEND_DIR' && echo -e '${GREEN}Frontend Development Server Starting...${NC}' && echo -e '${CYAN}Frontend will be available at: http://localhost:5173${NC}' && echo '' && npm run dev"
open_terminal "Frontend Dev Server" "$FRONTEND_CMD"
sleep 2

echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   All components started!          ${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo -e "${CYAN}Services:${NC}"
echo -e "  - Backend API:  http://localhost:8000"
echo -e "  - API Docs:     http://localhost:8000/docs"
echo -e "  - Frontend:     http://localhost:5173"
echo -e "  - Worker:       Running in background"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services...${NC}"

# Keep script running
while true; do
    sleep 1
done
