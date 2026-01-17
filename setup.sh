#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LibraryDown - Universal Social Media Downloader      ║${NC}"
echo -e "${BLUE}║                  Setup Script v2.0.0                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    PKG_MANAGER="apt-get"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    PKG_MANAGER="brew"
else
    echo -e "${RED}[ERROR] Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Detected OS: $OS${NC}"
echo ""

# --- 1. System Dependency Installation ---
echo -e "${BLUE}[STEP 1/6] Installing system dependencies...${NC}"

if [ "$OS" == "linux" ]; then
    echo "[INFO] Updating package list..."
    sudo apt-get update -qq
    
    echo "[INFO] Installing Python 3, pip, and Redis..."
    sudo apt-get install -y python3 python3-pip python3-venv redis-server > /dev/null
    
    echo "[INFO] Starting Redis server..."
    sudo systemctl enable redis-server > /dev/null 2>&1 || true
    sudo systemctl start redis-server > /dev/null 2>&1 || true
    
elif [ "$OS" == "mac" ]; then
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}[ERROR] Homebrew not found. Please install: https://brew.sh${NC}"
        exit 1
    fi
    
    echo "[INFO] Installing Python and Redis via Homebrew..."
    brew install python redis > /dev/null 2>&1 || true
    
    echo "[INFO] Starting Redis service..."
    brew services start redis > /dev/null 2>&1 || true
fi

echo -e "${GREEN}[✓] System dependencies installed${NC}"
echo ""

# --- 2. Python Virtual Environment Setup ---
echo -e "${BLUE}[STEP 2/6] Setting up Python virtual environment...${NC}"

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment at './$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}[✓] Virtual environment created${NC}"
else
    echo -e "${YELLOW}[!] Virtual environment already exists${NC}"
fi

echo "[INFO] Activating virtual environment..."
source $VENV_DIR/bin/activate

echo -e "${GREEN}[✓] Virtual environment activated${NC}"
echo ""

# --- 3. Python Dependencies Installation ---
echo -e "${BLUE}[STEP 3/6] Installing Python dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing packages from requirements.txt..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    echo -e "${GREEN}[✓] Python dependencies installed${NC}"
else
    echo -e "${RED}[ERROR] requirements.txt not found!${NC}"
    exit 1
fi

echo ""

# --- 4. Environment File Setup ---
echo -e "${BLUE}[STEP 4/6] Configuring environment variables...${NC}"

if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}[✓] .env file created${NC}"
    echo -e "${YELLOW}[!] Please review and update .env file with your settings${NC}"
else
    echo -e "${YELLOW}[!] .env file already exists (skipping)${NC}"
fi

echo ""

# --- 5. Directory Setup ---
echo -e "${BLUE}[STEP 5/6] Creating necessary directories...${NC}"

mkdir -p media
mkdir -p logs
mkdir -p docs

# Create .gitkeep for media folder
touch media/.gitkeep

echo -e "${GREEN}[✓] Directories created${NC}"
echo ""

# --- 6. Database Initialization ---
echo -e "${BLUE}[STEP 6/6] Initializing database...${NC}"

echo "[INFO] Database will be created automatically on first run"
echo -e "${GREEN}[✓] Setup ready${NC}"
echo ""

# --- Redis Connection Test ---
echo -e "${BLUE}[TESTING] Checking Redis connection...${NC}"

if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}[✓] Redis is running and accessible${NC}"
else
    echo -e "${YELLOW}[!] Warning: Cannot connect to Redis${NC}"
    echo -e "${YELLOW}    Please ensure Redis is running: redis-server${NC}"
fi

echo ""

# --- Setup Complete ---
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🎉 SETUP COMPLETED SUCCESSFULLY! 🎉          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Activate the virtual environment:${NC}"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "2. ${YELLOW}Start Redis server (if not running):${NC}"
echo -e "   ${GREEN}redis-server${NC}"
echo ""
echo -e "3. ${YELLOW}Start Celery Worker (Terminal 1):${NC}"
echo -e "   ${GREEN}celery -A src.workers.celery_app worker --loglevel=info${NC}"
echo ""
echo -e "4. ${YELLOW}Start Celery Beat (Terminal 2):${NC}"
echo -e "   ${GREEN}celery -A src.workers.celery_app beat --loglevel=info${NC}"
echo ""
echo -e "5. ${YELLOW}Start FastAPI Server (Terminal 3):${NC}"
echo -e "   ${GREEN}uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo -e "6. ${YELLOW}Access the API:${NC}"
echo -e "   ${GREEN}http://localhost:8000/docs${NC} (Swagger UI)"
echo -e "   ${GREEN}http://localhost:8000/redoc${NC} (ReDoc)"
echo ""
echo -e "${BLUE}For more information, see:${NC}"
echo -e "   • ${GREEN}README.md${NC} - General documentation"
echo -e "   • ${GREEN}docs/API.md${NC} - API documentation"
echo -e "   • ${GREEN}docs/ROADMAP.md${NC} - Project roadmap"
echo ""
echo -e "${BLUE}Happy downloading! 🚀${NC}"
echo ""
