# Contributing to LibraryDown

Thank you for considering contributing to LibraryDown! This guide will help you get started with contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code of Conduct](#code-of-conduct)

## Getting Started

### Prerequisites
- Python 3.11+
- Redis server
- Git
- FFmpeg (for media processing)

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/librarydown.git
   cd librarydown
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Install development dependencies:
   ```bash
   pip install pytest pytest-asyncio black flake8 mypy
   ```

6. Create your local `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Project Structure

```
librarydown/
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
│   └── fixtures/                # Test fixtures
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── guides/                  # User guides
│   ├── security/                # Security docs
│   └── development/             # Development guides
├── scripts/                     # Utility scripts
│   ├── setup/                   # Setup scripts
│   ├── deploy/                  # Deployment scripts
│   ├── systemd/                 # Systemd service files
│   ├── security/                # Security scripts
│   └── utils/                   # Utility scripts
├── data/                        # Data files
│   ├── db/                      # Database files
│   ├── logs/                    # Log files
│   └── temp/                    # Temporary files
└── media/                       # Downloaded media files
```

## Development Workflow

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### Making Changes
1. Follow the [Coding Standards](#coding-standards)
2. Write tests for your changes
3. Update documentation as needed
4. Run tests to ensure everything works

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality Checks
```bash
# Format code
black src/

# Lint code
flake8 src/

# Type check
mypy src/
```

## Coding Standards

### Python Style
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use type hints for all function signatures
- Write docstrings for all public functions and classes

### Naming Conventions
- Use descriptive names
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

### File Organization
- Each platform should have its own file in `src/engine/platforms/`
- Keep files focused on single responsibility
- Group related functionality in the same module

### Error Handling
- Use custom exceptions from `src/utils/exceptions.py`
- Provide meaningful error messages
- Log errors appropriately with loguru

## Testing

### Test Structure
- Unit tests: Test individual functions and classes
- Integration tests: Test interactions between components
- End-to-end tests: Test complete workflows

### Writing Tests
- Use pytest for all tests
- Follow AAA pattern (Arrange, Act, Assert)
- Use descriptive test names
- Test both happy path and error cases
- Use fixtures for common test setup

### Test Categories

#### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution

#### Integration Tests (`tests/integration/`)
- Test component interactions
- May use real database/filesystem
- Moderate execution time

#### End-to-End Tests (`tests/e2e/`)
- Test complete user workflows
- Use real services where possible
- May take longer to execute

## Security Considerations

### Input Validation
- Always validate and sanitize user inputs
- Use the security utilities in `src/utils/security.py`
- Implement proper URL validation
- Prevent path traversal attacks

### Credential Handling
- Never commit real credentials
- Use environment variables for sensitive data
- Follow the security guidelines in the README

## Submitting Changes

### Commit Messages
- Use conventional commit format:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `refactor:` for code restructuring
  - `docs:` for documentation
  - `test:` for tests
  - `chore:` for maintenance

Example:
```
feat: Add TikTok video download functionality

- Implement TikTokDownloader class
- Add TikTok-specific URL detection
- Handle TikTok's API response format
- Add corresponding tests
```

### Pull Request Process
1. Ensure all tests pass
2. Update documentation if needed
3. Squash commits if necessary
4. Submit pull request with clear description
5. Address review comments
6. Wait for approval before merging

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Code is maintainable and readable
- [ ] Performance impacts are considered

## Code of Conduct

This project adheres to the Python Community Code of Conduct. By participating, you are expected to follow these guidelines:

- Be respectful and inclusive
- Provide constructive feedback
- Respect differences of opinion
- Focus on what is best for the community

## Questions?

If you have questions about contributing, feel free to open an issue or reach out to the maintainers.

Happy coding! 🎉