# Contributing to Magical Emporium

Thank you for your interest in contributing to the Magical Emporium! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Submitting Issues](#submitting-issues)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Project Structure](#project-structure)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions
- Have fun building magical things!

## Getting Started

Before contributing, make sure you have:

1. **Python 3.11+** installed on your system
2. **UV package manager** installed ([installation guide](https://github.com/astral-sh/uv))
3. **Git** for version control
4. A **Google Gemini API key** for testing (get one at [ai.google.dev](https://ai.google.dev/))

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/magic-shop.git
cd magic-shop

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/magic-shop.git
```

### 2. Install Dependencies

```bash
# Install all dependencies including dev dependencies
uv sync
```

This will create a virtual environment and install:
- All production dependencies
- Development tools (pytest, ruff)

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
# Required for integration tests:
GEMINI_API_KEY=your_api_key_here
ADMIN_PASSWORD=test-password-for-dev
DATA_DIR=/tmp/magic-shop-dev
```

### 4. Initialize the Database

```bash
# Run the application once to create the database
uv run uvicorn app.main:app --reload
# Press Ctrl+C after it starts
```

### 5. Verify Setup

```bash
# Run tests to verify everything is working
uv run pytest -m "not integration"

# If you have a valid API key, run all tests
uv run pytest
```

## Running Tests

We use pytest for testing. Tests are organized by type:

### Run All Tests

```bash
uv run pytest
```

### Run Only Unit Tests (Fast)

Skip integration tests that require API calls:

```bash
uv run pytest -m "not integration"
```

### Run Only Integration Tests

Requires valid `GEMINI_API_KEY`:

```bash
uv run pytest -m integration
```

### Run with Coverage

```bash
# Generate coverage report
uv run pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Specific Test File

```bash
uv run pytest tests/test_models.py
```

### Run Specific Test

```bash
uv run pytest tests/test_models.py::test_create_product_with_all_fields
```

### Run with Verbose Output

```bash
uv run pytest -v
```

## Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. Ruff is an extremely fast Python linter and formatter written in Rust.

### Configuration

Ruff is configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = []
```

### Check for Issues

```bash
# Check all Python files
uv run ruff check .

# Check specific file
uv run ruff check app/main.py
```

### Auto-Fix Issues

```bash
# Fix all auto-fixable issues
uv run ruff check --fix .

# Fix specific file
uv run ruff check --fix app/main.py
```

### Format Code

```bash
# Format all Python files
uv run ruff format .

# Format specific file
uv run ruff format app/main.py

# Check formatting without making changes
uv run ruff format --check .
```

### Before Committing

Always run both checks and formatting:

```bash
# Check and fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Run tests
uv run pytest -m "not integration"
```

### Style Guidelines

- **Line length**: Maximum 100 characters
- **Imports**: Sorted and organized (Ruff will handle this)
- **Naming conventions**:
  - Functions and variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
  - Private/internal: `_leading_underscore`
- **Docstrings**: Use for all public functions, classes, and modules
- **Type hints**: Encouraged but not required (especially for public APIs)
- **Comments**: Explain "why", not "what" (code should be self-documenting)

## Making Changes

### Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes** following the code style guidelines

3. **Write tests** for new functionality:
   - Add unit tests in the appropriate `tests/test_*.py` file
   - Add integration tests if needed (mark with `@pytest.mark.integration`)

4. **Run tests and linting**:
   ```bash
   uv run ruff check --fix .
   uv run ruff format .
   uv run pytest -m "not integration"
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

   Commit message guidelines:
   - Use present tense ("Add feature" not "Added feature")
   - First line: concise summary (50 chars or less)
   - Optionally add detailed description after blank line
   - Reference issue numbers if applicable: "Fixes #123"

6. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### What to Work On

- Check the [Issues](https://github.com/ORIGINAL_OWNER/magic-shop/issues) page for open issues
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Look for issues labeled `help wanted` for areas needing contribution
- Propose new features by opening an issue first for discussion

## Submitting Issues

### Bug Reports

When submitting a bug report, please include:

1. **Clear title**: Concise description of the issue
2. **Description**: Detailed explanation of the problem
3. **Steps to reproduce**:
   ```
   1. Go to '...'
   2. Click on '...'
   3. See error
   ```
4. **Expected behavior**: What should happen
5. **Actual behavior**: What actually happens
6. **Environment**:
   - OS (Windows, macOS, Linux)
   - Python version (`python --version`)
   - UV version (`uv --version`)
   - Docker version (if applicable)
7. **Logs**: Relevant error messages or logs
   ```bash
   docker-compose logs magic-shop
   ```
8. **Screenshots**: If applicable

### Feature Requests

When proposing a new feature:

1. **Clear title**: Brief description of the feature
2. **Use case**: Explain why this feature would be useful
3. **Proposed solution**: How you think it should work
4. **Alternatives considered**: Other approaches you've thought about
5. **Additional context**: Mockups, examples, references

## Submitting Pull Requests

### Before Submitting

- [ ] Code follows the style guidelines (Ruff passes)
- [ ] Tests pass (`pytest -m "not integration"`)
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, docstrings, comments)
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up-to-date with main

### Pull Request Process

1. **Create the PR** on GitHub from your fork

2. **Fill in the template** with:
   - **Title**: Clear, concise description of changes
   - **Description**:
     - What does this PR do?
     - Why is this change needed?
     - Related issue numbers (Fixes #123)
   - **Testing**: How to test the changes
   - **Screenshots**: If UI changes are involved

3. **Review process**:
   - Maintainers will review your code
   - Address any feedback or requested changes
   - Push updates to your branch (they'll appear in the PR automatically)

4. **Merge**:
   - Once approved, a maintainer will merge your PR
   - Your changes will be in the next release!

### PR Guidelines

- **Keep it focused**: One PR should address one issue or feature
- **Small is better**: Smaller PRs are easier to review and merge
- **Update docs**: If you change functionality, update relevant documentation
- **Test thoroughly**: Make sure your changes don't break existing functionality
- **Be responsive**: Reply to review comments and make requested changes

## Project Structure

Understanding the codebase:

```
app/
├── main.py              # FastAPI app initialization, lifespan events
├── config.py            # Configuration management (YAML + env vars)
├── database.py          # Database setup and session management
├── logger.py            # Logging configuration
├── models/
│   └── product.py       # SQLAlchemy Product model
├── routes/
│   ├── public.py        # Public storefront routes (/, /product/{id})
│   └── admin.py         # Admin routes (/admin/*, authentication)
├── services/
│   ├── gemini.py        # Gemini API client (text + image generation)
│   ├── image.py         # Image processing (PNG to JPG conversion)
│   └── product.py       # Product business logic (CRUD, AI orchestration)
├── static/              # Static files (CSS, images served from /data)
│   └── css/
│       └── style.css    # Whimsical magical theme styles
└── templates/           # Jinja2 HTML templates
    ├── base.html        # Base template for public pages
    ├── index.html       # Product catalog homepage
    ├── product.html     # Product detail page
    └── admin/
        ├── base.html    # Base template for admin pages
        ├── list.html    # Admin product list
        └── new.html     # Product creation form (with HTMX)
```

### Key Concepts

- **Configuration**: `config.py` loads from `config.yaml` and environment variables
- **Database**: SQLAlchemy with SQLite, session managed by `database.py`
- **Services**: Business logic separated from routes
- **Routes**: FastAPI routers with Jinja2 templates
- **Templates**: HTMX for dynamic product creation without page reloads
- **Authentication**: HTTP Basic Auth for admin routes

## Development Tips

### Running Locally

```bash
# Start with auto-reload
uv run uvicorn app.main:app --reload

# Access at http://localhost:8000
# Admin at http://localhost:8000/admin (username: admin, password: from .env)
```

### Viewing Logs

```bash
# The logger outputs to console by default
# Set log level in config.yaml:
settings:
  log_level: DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Testing with Docker

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f magic-shop

# Stop
docker-compose down

# Clean up (removes volumes)
docker-compose down -v
```

### Database Inspection

```bash
# Install sqlite3 if not available
# Then inspect the database:
sqlite3 data/store.db

# Common queries:
sqlite> .tables
sqlite> SELECT * FROM products;
sqlite> .schema products
sqlite> .quit
```

## Questions?

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the README.md and code docstrings

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Magical Emporium! Your help makes this project more magical for everyone.
