# Magical Emporium

A whimsical fictional magic item store website with AI-generated products using Google Gemini. Browse enchanted artifacts, mystical potions, and legendary items - all perpetually out of stock due to their extreme rarity!

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

## Features

- **Public Storefront**: Browse a catalog of magical items with beautiful AI-generated images and descriptions
- **AI-Powered Content**: Each product is generated using Google Gemini 2.0 for descriptions and Gemini 2.5 Flash Image (Nano Banana) for images
- **Admin Panel**: Simple interface to create new products from one-line descriptions
- **Whimsical Design**: Magical shop theme with enchanting visual elements
- **Persistent Storage**: SQLite database with image storage
- **Docker-Ready**: Easy deployment with Docker Compose
- **Configurable**: Editable system prompts via YAML configuration

All items are marked as "Out of Stock" because, of course, magical artifacts of this caliber are exceedingly rare!

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- A **Google Gemini API key** ([Get your API key](https://ai.google.dev/))

## Quick Start

Get the Magical Emporium running in just a few steps:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/magic-shop.git
cd magic-shop
```

### 2. Configure Environment Variables

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and set the following:

```bash
# Your Google Gemini API key (required)
GEMINI_API_KEY=your_actual_api_key_here

# Admin password for accessing /admin (required)
ADMIN_PASSWORD=your_secure_password_here

# Data directory (optional, defaults to /data)
DATA_DIR=/data
```

**Important**: Use a strong password for `ADMIN_PASSWORD`. Anyone with this password can create products in your shop.

### 3. Start the Application

```bash
docker-compose up -d
```

This command will:
- Build the Docker image
- Start the container in detached mode
- Create the database and data directories
- Make the application available at http://localhost:8000

### 4. Access Your Magic Shop

- **Public Storefront**: Visit http://localhost:8000
- **Admin Panel**: Visit http://localhost:8000/admin
  - Username: `admin` (or any username)
  - Password: The value you set for `ADMIN_PASSWORD` in `.env`

### 5. Create Your First Product

1. Navigate to http://localhost:8000/admin
2. Click "Create New Product"
3. Enter a one-line description (e.g., "A glowing crystal orb that shows visions of the future")
4. Click "Generate Product" and wait 10-30 seconds
5. Your magical item will appear with an AI-generated description and image!

## Configuration

### System Prompts

You can customize how the AI generates content by editing `config.yaml`:

```yaml
system_prompts:
  description_generation: |
    You are a creative writer for a magical item shop. Generate whimsical,
    enchanting descriptions for rare and magical items. Emphasize their
    mystical properties, legendary origins, and extreme rarity. Write in
    an engaging, story-like style that makes each item feel precious and
    unique. Keep descriptions between 100-200 words.

  image_prompt_generation: |
    Based on the following magical item description, create a detailed
    image generation prompt that captures the visual essence of the item.
    Include details about appearance, magical effects, materials, and
    atmosphere. Make it vivid and specific.

settings:
  data_dir: /data
  image_size: 1024
  log_level: INFO
```

**After editing `config.yaml`**: Restart the container for changes to take effect:

```bash
docker-compose restart
```

### Application Settings

The `settings` section in `config.yaml` controls:

- **data_dir**: Where the SQLite database and images are stored (default: `/data`)
- **image_size**: Size of generated images in pixels (default: `1024` for 1024x1024)
- **log_level**: Logging verbosity - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

## Development

### Running Locally with UV

For development without Docker:

#### 1. Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Install Dependencies

```bash
uv sync
```

#### 3. Set Environment Variables

```bash
# Create .env file (as shown in Quick Start)
export $(cat .env | xargs)
```

#### 4. Run the Application

```bash
uv run uvicorn app.main:app --reload
```

The app will be available at http://localhost:8000 with auto-reload on code changes.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run only unit tests (skip integration tests that require API credentials)
uv run pytest -m "not integration"

# Run only integration tests
uv run pytest -m integration
```

**Note**: Integration tests require valid `GEMINI_API_KEY` environment variable and will make real API calls.

### Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Deployment

### Deploying Behind a Reverse Proxy

For production, you should run the Magical Emporium behind a reverse proxy (like Nginx or Caddy) that handles:
- TLS/SSL termination (HTTPS)
- Domain routing
- Rate limiting
- Static file caching

#### Example Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name magic-shop.example.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/magic-shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magic-shop.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for long AI generation requests
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Cache static files
    location /static/ {
        proxy_pass http://localhost:8000/static/;
        proxy_cache_valid 200 7d;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name magic-shop.example.com;
    return 301 https://$server_name$request_uri;
}
```

#### Docker Compose for Production

Modify `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  magic-shop:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: magic-shop
    ports:
      - "127.0.0.1:8000:8000"  # Only expose on localhost
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - DATA_DIR=/data
    volumes:
      - ./data:/data
      - ./config.yaml:/app/config.yaml:ro
      - ./data/images:/app/static/images
    restart: always  # Always restart in production
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Production Checklist

- [ ] Use a strong `ADMIN_PASSWORD` (20+ characters, random)
- [ ] Store `.env` file securely (never commit to Git)
- [ ] Set up HTTPS with valid SSL certificates
- [ ] Configure firewall to only allow necessary ports
- [ ] Set up automated backups of `/data` directory
- [ ] Monitor logs for errors: `docker-compose logs -f magic-shop`
- [ ] Set `log_level: WARNING` or `ERROR` in production
- [ ] Consider adding rate limiting to the reverse proxy
- [ ] Set up monitoring/alerting for the application

## Troubleshooting

### Container won't start

**Problem**: Docker container fails to start or immediately exits.

**Solutions**:
```bash
# Check the logs
docker-compose logs magic-shop

# Common issues:
# 1. Missing environment variables - verify .env file exists and is valid
# 2. Port 8000 already in use - change ports in docker-compose.yml
# 3. Permission issues - ensure data directory is writable
```

### "Configuration error" when accessing admin

**Problem**: Admin page shows configuration error.

**Solutions**:
- Verify `GEMINI_API_KEY` and `ADMIN_PASSWORD` are set in `.env`
- Check `.env` file is in the same directory as `docker-compose.yml`
- Restart container: `docker-compose restart`
- Verify environment variables are loaded: `docker-compose exec magic-shop env | grep GEMINI`

### Product generation fails

**Problem**: Product creation shows error or times out.

**Solutions**:
```bash
# Check API key is valid
# Visit https://ai.google.dev/ to verify your API key

# Check logs for specific errors
docker-compose logs -f magic-shop

# Common issues:
# 1. Invalid API key - get a new one from https://ai.google.dev/
# 2. API quota exceeded - check your Gemini API usage
# 3. Network connectivity - ensure container can reach Gemini API
# 4. Timeout - image generation can take 20-30 seconds, be patient
```

### Images not displaying

**Problem**: Product images show as broken links.

**Solutions**:
```bash
# Verify image directory exists and is writable
ls -la ./data/images

# Check volume mount in docker-compose.yml
docker-compose down
docker-compose up -d

# Verify images exist
docker-compose exec magic-shop ls -la /data/images
docker-compose exec magic-shop ls -la /app/static/images
```

### Database corruption

**Problem**: Database errors or data not persisting.

**Solutions**:
```bash
# Backup current database
cp ./data/store.db ./data/store.db.backup

# Stop container
docker-compose down

# Remove corrupted database (this will delete all products!)
rm ./data/store.db

# Restart (will create fresh database)
docker-compose up -d
```

### Permission denied errors

**Problem**: Container can't write to data directory.

**Solutions**:
```bash
# Fix permissions on data directory
chmod -R 755 ./data
chown -R $(whoami):$(whoami) ./data

# Restart container
docker-compose restart
```

### Admin authentication not working

**Problem**: Correct password is rejected.

**Solutions**:
- Ensure `ADMIN_PASSWORD` in `.env` matches what you're typing
- Check for extra spaces or hidden characters in `.env`
- Password is case-sensitive
- Try setting a simple password to test, then change to secure one
- Restart container after changing `.env`: `docker-compose restart`

### High memory usage

**Problem**: Container using excessive memory.

**Solutions**:
```bash
# Monitor container resources
docker stats magic-shop

# Add memory limits to docker-compose.yml:
services:
  magic-shop:
    # ... other config ...
    mem_limit: 1g
    memswap_limit: 1g
```

### Logs filling up disk

**Problem**: Docker logs consuming too much space.

**Solutions**:
```bash
# Check log size
docker-compose logs magic-shop | wc -l

# Configure log rotation in docker-compose.yml (shown in Production section above)

# Clear existing logs
docker-compose down
docker system prune -f
```

### Still having issues?

1. **Check the logs**: `docker-compose logs -f magic-shop`
2. **Search existing issues**: Check the GitHub Issues page
3. **Create an issue**: Provide logs, your `.env` (without secrets), and steps to reproduce

## Project Structure

```
magic-shop/
├── app/                    # Application code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── database.py        # Database setup and session management
│   ├── logger.py          # Logging configuration
│   ├── models/            # SQLAlchemy models
│   │   └── product.py     # Product model
│   ├── routes/            # API routes
│   │   ├── public.py      # Public storefront routes
│   │   └── admin.py       # Admin panel routes
│   ├── services/          # Business logic
│   │   ├── gemini.py      # Gemini API client
│   │   ├── image.py       # Image processing
│   │   └── product.py     # Product service
│   ├── static/            # Static files (CSS, JS)
│   │   └── css/
│   │       └── style.css
│   └── templates/         # Jinja2 HTML templates
│       ├── base.html
│       ├── index.html
│       ├── product.html
│       └── admin/
│           ├── base.html
│           ├── list.html
│           └── new.html
├── tests/                 # Test suite
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_gemini.py
│   ├── test_image.py
│   ├── test_product_service.py
│   └── test_integration.py
├── data/                  # Persistent data (not in Git)
│   ├── store.db          # SQLite database
│   └── images/           # Generated product images
├── config.yaml           # System prompts and settings
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker image definition
├── pyproject.toml       # Python project configuration
├── uv.lock             # UV dependency lock file
├── .env.example        # Example environment variables
└── README.md           # This file
```

## Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: Google Gemini 2.0 (text) and Gemini 2.5 Flash Image (images)
- **Frontend**: Jinja2 templates with HTMX for dynamic interactions
- **Styling**: Custom CSS with magical theme
- **Image Processing**: Pillow (PIL)
- **Package Manager**: UV
- **Containerization**: Docker and Docker Compose

## API Endpoints

### Public Routes

- `GET /` - Product catalog homepage
- `GET /product/{id}` - Individual product detail page
- `GET /health` - Health check endpoint (returns `{"status": "healthy"}`)

### Admin Routes (require authentication)

- `GET /admin` - Admin product list
- `GET /admin/new` - New product creation form
- `POST /admin/create` - Create product from description (HTMX endpoint)

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024 Magical Emporium

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Google Gemini](https://ai.google.dev/)
- Package management by [UV](https://github.com/astral-sh/uv)
- Styled with inspiration from magical and whimsical design patterns

---

**Enjoy your Magical Emporium!** May your enchanted items bring wonder and delight to all who visit your mystical storefront.
