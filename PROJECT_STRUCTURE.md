# LibraryDown Project Structure

This document describes the organized directory structure of the LibraryDown project.

## Root Directory
```
librarydown/
├── README.md                     # Main project documentation
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore patterns
├── Dockerfile                   # Docker build configuration
├── docker-compose.yml           # Docker Compose configuration
├── celerybeat-schedule          # Celery schedule file
├── media/                       # Media files directory
│   └── .gitkeep
├── cookies/                     # Cookie files directory
│   └── .gitkeep
├── src/                         # Source code
│   ├── api/                     # FastAPI application
│   ├── core/                    # Core configuration
│   ├── database/                # Database layer
│   ├── engine/                  # Download engine
│   │   └── platforms/           # Platform implementations
│   ├── utils/                   # Utility modules
│   └── workers/                 # Celery workers
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end tests
│   └── fixtures/                # Test fixtures and conftest
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── guides/                  # User guides
│   ├── security/                # Security documentation
│   └── development/             # Development guides
├── scripts/                     # Scripts
│   ├── setup/                   # Setup scripts
│   ├── deploy/                  # Deployment scripts
│   ├── systemd/                 # Systemd service files
│   ├── security/                # Security scripts
│   └── utils/                   # Utility scripts
├── data/                        # Data files
│   ├── db/                      # Database files
│   ├── logs/                    # Log files
│   └── temp/                    # Temporary files
└── venv/                        # Virtual environment
```

## Directory Purposes

### `src/` - Source Code
- `api/`: FastAPI application, endpoints, and schemas
- `core/`: Core configuration and settings
- `database/`: Database models, connections, and base
- `engine/`: Core download engine and platform implementations
- `utils/`: Shared utility modules (security, caching, etc.)
- `workers/`: Celery tasks and worker configuration

### `tests/` - Test Suite
- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for combined components
- `e2e/`: End-to-end tests for complete workflows
- `fixtures/`: Test fixtures and configuration

### `docs/` - Documentation
- `api/`: API-specific documentation
- `guides/`: User and setup guides
- `security/`: Security-related documentation
- `development/`: Development guides and contributing

### `scripts/` - Utility Scripts
- `setup/`: Initial setup and installation scripts
- `deploy/`: Deployment and management scripts
- `systemd/`: Systemd service configuration files
- `security/`: Security-related scripts
- `utils/`: General utility scripts

### `data/` - Data Storage
- `db/`: Database files and backups
- `logs/`: Log files
- `temp/`: Temporary files (should be in .gitignore)