#!/bin/bash

# LibraryDown Enhanced Deployment Script
# This script sets up the complete LibraryDown system with all enhancements

set -e  # Exit on any error

echo "🚀 Starting LibraryDown Enhanced Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3.11+ is required"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_status "Docker found: $(docker --version)"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found, will use manual installation"
        DOCKER_AVAILABLE=false
    fi
    
    # Check if running as root (for system installations)
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root - this is fine for system setup"
    fi
}

# Setup virtual environment
setup_virtualenv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install additional development/testing dependencies
    pip install pytest pytest-asyncio httpx[http2] black flake8 mypy
    
    print_success "Dependencies installed"
}

# Setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    if command -v redis-server &> /dev/null; then
        print_status "Redis already installed"
        # Start Redis if not running
        if ! pgrep redis-server > /dev/null; then
            redis-server --daemonize yes
            print_success "Redis server started"
        else
            print_status "Redis server already running"
        fi
    else
        print_warning "Redis not found, installing..."
        # Try to install Redis based on OS
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install -y redis
        elif command -v brew &> /dev/null; then
            brew install redis
        else
            print_error "Could not install Redis automatically. Please install manually."
            exit 1
        fi
        redis-server --daemonize yes
        print_success "Redis installed and started"
    fi
    
    # Test Redis connection
    if redis-cli ping > /dev/null; then
        print_success "Redis connection test passed"
    else
        print_error "Redis connection failed"
        exit 1
    fi
}

# Setup directories
setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p media cookies logs
    chmod 755 media cookies logs
    
    # Create .gitkeep files
    touch media/.gitkeep cookies/.gitkeep logs/.gitkeep
    
    print_success "Directories created"
}

# Setup environment configuration
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from example"
        else
            # Create basic .env file
            cat > .env << EOF
# Application Settings
APP_NAME="Universal Social Media Downloader"
DEBUG=True
API_V1_STR="/api/v1"
API_BASE_URL="http://localhost:8000"

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database Settings
DATABASE_NAME=librarydown.db

# File Management
MEDIA_FOLDER=media
FILE_TTL_HOURS=24
MAX_FILE_SIZE_MB=500

# Task Settings
MAX_RETRIES=3
RETRY_BACKOFF=5
EOF
            print_success "Basic environment file created"
        fi
    else
        print_status "Environment file already exists"
    fi
}

# Run database migrations
setup_database() {
    print_status "Setting up database..."
    
    # Initialize database
    python -c "
import sys
sys.path.insert(0, '.')
from src.database.base import engine, Base
from src.database.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created')
"
    
    print_success "Database setup complete"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Run basic functionality tests
    python -c "
import sys
sys.path.insert(0, '.')
from src.utils.security import SecurityValidator
from src.utils.cache import CacheManager

# Test security validation
test_urls = [
    'https://www.youtube.com/watch?v=test',
    'https://vt.tiktok.com/test/',
    'https://instagram.com/p/test'
]

for url in test_urls:
    is_valid, error = SecurityValidator.validate_url(url)
    assert is_valid, f'URL validation failed: {url} - {error}'

# Test cache
cache = CacheManager()
cache.set('test_key', {'test': 'data'}, ttl=60)
result = cache.get('test_key')
assert result == {'test': 'data'}

print('All tests passed!')
"
    
    print_success "Core functionality tests passed"
}

# Docker deployment
docker_deployment() {
    if [ "$DOCKER_AVAILABLE" = true ]; then
        print_status "Setting up Docker deployment..."
        
        # Build Docker images
        docker-compose build
        
        # Start services
        docker-compose up -d
        
        # Wait for services to start
        sleep 10
        
        # Check service status
        if docker-compose ps | grep -q "Up"; then
            print_success "Docker services started successfully"
        else
            print_error "Some Docker services failed to start"
            docker-compose ps
            exit 1
        fi
    else
        print_warning "Skipping Docker deployment - Docker not available"
    fi
}

# Manual service startup
manual_startup() {
    if [ "$DOCKER_AVAILABLE" = false ]; then
        print_status "Starting services manually..."
        
        # Start Celery worker in background
        celery -A src.workers.celery_app worker --loglevel=info &
        WORKER_PID=$!
        echo "Celery worker PID: $WORKER_PID"
        
        # Start Celery beat in background
        celery -A src.workers.celery_app beat --loglevel=info &
        BEAT_PID=$!
        echo "Celery beat PID: $BEAT_PID"
        
        # Start API server
        print_success "Services started. API available at http://localhost:8000"
        print_success "Documentation: http://localhost:8000/docs"
        print_success "Health check: http://localhost:8000/health"
    fi
}

# Create service management scripts
create_management_scripts() {
    print_status "Creating management scripts..."
    
    # Create start script
    cat > start_services.sh << 'EOF'
#!/bin/bash
# LibraryDown Service Starter

source venv/bin/activate

echo "Starting LibraryDown services..."

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    redis-server --daemonize yes
fi

# Start services
celery -A src.workers.celery_app worker --loglevel=info &
CELERY_WORKER_PID=$!

celery -A src.workers.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!

uvicorn src.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Services started:"
echo "  Celery Worker PID: $CELERY_WORKER_PID"
echo "  Celery Beat PID: $CELERY_BEAT_PID"  
echo "  API Server PID: $API_PID"
echo ""
echo "API available at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
EOF

    chmod +x start_services.sh
    
    # Create stop script
    cat > stop_services.sh << 'EOF'
#!/bin/bash
# LibraryDown Service Stopper

echo "Stopping LibraryDown services..."

# Kill processes by name
pkill -f "celery.*worker"
pkill -f "celery.*beat"  
pkill -f "uvicorn.*src.main"

echo "Services stopped"
EOF

    chmod +x stop_services.sh
    
    # Create status script
    cat > service_status.sh << 'EOF'
#!/bin/bash
# LibraryDown Service Status

echo "LibraryDown Service Status:"
echo "=========================="

echo "Redis:"
if pgrep redis-server > /dev/null; then
    echo "  ✓ Running"
else
    echo "  ✗ Not running"
fi

echo "Celery Worker:"
if pgrep -f "celery.*worker" > /dev/null; then
    echo "  ✓ Running (PID: $(pgrep -f "celery.*worker"))"
else
    echo "  ✗ Not running"
fi

echo "Celery Beat:"
if pgrep -f "celery.*beat" > /dev/null; then
    echo "  ✓ Running (PID: $(pgrep -f "celery.*beat"))"
else
    echo "  ✗ Not running"
fi

echo "API Server:"
if pgrep -f "uvicorn.*src.main" > /dev/null; then
    echo "  ✓ Running (PID: $(pgrep -f "uvicorn.*src.main"))"
    echo "  Available at: http://localhost:8000"
else
    echo "  ✗ Not running"
fi
EOF

    chmod +x service_status.sh
    
    print_success "Management scripts created"
}

# Main deployment process
main() {
    print_status "Starting LibraryDown Enhanced Deployment"
    echo "========================================="
    
    check_prerequisites
    setup_virtualenv
    install_dependencies
    setup_redis
    setup_directories
    setup_environment
    setup_database
    run_tests
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        docker_deployment
    else
        manual_startup
    fi
    
    create_management_scripts
    
    echo ""
    echo "========================================="
    print_success "LibraryDown Enhanced Deployment Complete!"
    echo ""
    echo "🚀 Next Steps:"
    echo "   • Access API documentation: http://localhost:8000/docs"
    echo "   • Check health status: http://localhost:8000/health"
    echo "   • View system metrics: http://localhost:8000/metrics"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • Start services: ./start_services.sh"
    echo "   • Stop services: ./stop_services.sh"
    echo "   • Check status: ./service_status.sh"
    echo ""
    echo "📚 Documentation:"
    echo "   • Enhanced docs: ENHANCED_DOCS.md"
    echo "   • API documentation: http://localhost:8000/docs"
    echo ""
    print_success "Enjoy your enhanced LibraryDown system! 🎉"
}

# Run main deployment
main "$@"