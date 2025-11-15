# Magic Shop - Project Planning Documentation

## Project Overview

A whimsical fictional magic item store website with AI-generated products using Google Gemini.

## Step 1: Problem Understanding

### Concise Project Summary

A whimsical fictional magic item store website with two sides: a public storefront where visitors can browse magical items (all marked as "out of stock" due to their rare nature), and an admin interface where you can create new products by providing a one-line description. The backend uses Google Gemini to generate magical, rare-focused product descriptions and the Gemini 2.5 Flash Image model (Nano Banana) to create product images.

**Key Stakeholders**: Creator/admin and visitors who enjoy whimsical, creative content

**Success Criteria**:
- Public users can browse a catalog of magical items with AI-generated descriptions and images
- Admin can create new products via simple one-line descriptions
- All products show greyed-out "Out of Stock" buy buttons
- Site is functional, deployed, and shareable

### MoSCoW Analysis for MVP

**Must Have**:
- Public storefront page displaying products in a browsable grid/list
- Product detail view showing description, image, and greyed-out "Out of Stock" button
- Admin interface with simple form to enter one-line product description
- Backend integration with Google Gemini API for description generation (with magic/rarity system prompt)
- Backend integration with Gemini 2.5 Flash Image (Nano Banana) for image generation
- SQLite database to store products (name, description, image path, price, category, tags, rarity)
- Image storage in a persistent data directory
- Basic admin authentication (HTTP Basic Auth)
- Docker containerization

**Should Have** (next version):
- Product categories/tags for better browsing
- Search functionality on storefront
- Ability to edit/delete products in admin
- Better admin UI
- Responsive mobile design
- Product pagination for large catalogs

**Could Have** (future consideration):
- Multiple admin users
- Product versioning/history
- Share product links on social media
- "Notify me when in stock" joke feature
- Whimsical animations and effects
- Dark mode themed as "moonlit shop"

**Won't Have** (explicitly out of scope):
- Real e-commerce functionality (no actual payments)
- User accounts for browsing (public is anonymous)
- Shopping cart
- Product reviews or ratings
- Multi-language support
- Advanced image editing or regeneration options in MVP

### Constraints

**Required Technologies**:
- Backend: Python with FastAPI framework
- Database: SQLAlchemy ORM with SQLite
- AI Services: Google Gemini API (text) + Gemini 2.5 Flash Image (images)
- Package: `google-genai`
- Containerization: Docker

**Deployment**:
- Docker container running the application
- Application runs behind a TLS termination server (reverse proxy handles HTTPS)
- Persistent data directory mounted for SQLite database and images

**Storage**:
- SQLite database file in data directory
- Product images stored as files (PNG original, JPG served)

**Integration Requirements**:
- Google Gemini API access via `GEMINI_API_KEY` environment variable
- Image generation using streaming API pattern

**Security**:
- HTTP Basic Auth for admin
- TLS handled by upstream reverse proxy
- API keys stored as environment variables

---

## Step 2: Solution Analysis

### Problem Statement

Build a dual-interface web application (public storefront + admin panel) for a fictional magic item store. The admin creates products via one-line descriptions that are automatically enhanced with AI-generated descriptions and images. The public views a whimsical catalog where all items are perpetually "out of stock."

### Selected Solution: Hybrid FastAPI + HTMX

**Architecture**:
- FastAPI backend with Jinja2 templates
- HTMX library for dynamic partial page updates
- AI generation triggered via HTMX with loading states
- Async background tasks using FastAPI's BackgroundTasks
- Server returns HTML fragments for dynamic updates

**Justification**:
- Right-sized for the project (simple CRUD with modern UX)
- Better UX for AI generation (loading spinners without page reloads)
- Fast development (no frontend build pipeline)
- Single Docker container, simple deployment
- Python-focused development

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Container                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            FastAPI Application                         │ │
│  │  ┌──────────────┐      ┌──────────────┐              │ │
│  │  │   Public     │      │    Admin     │              │ │
│  │  │   Routes     │      │   Routes     │              │ │
│  │  └──────┬───────┘      └──────┬───────┘              │ │
│  │         └─────────┬───────────┘                       │ │
│  │         ┌─────────▼──────────┐                        │ │
│  │         │  Jinja2 + HTMX     │                        │ │
│  │         └────────────────────┘                        │ │
│  │  ┌──────────────┐      ┌──────────────┐              │ │
│  │  │   Service    │─────▶│   Gemini     │              │ │
│  │  │   Layer      │      │   Client     │              │ │
│  │  └──────┬───────┘      └──────────────┘              │ │
│  │  ┌──────▼───────┐                                     │ │
│  │  │  SQLAlchemy  │                                     │ │
│  │  └──────┬───────┘                                     │ │
│  └─────────┼──────────────────────────────────────────── │ │
└────────────┼───────────────────────────────────────────────┘
    ┌────────▼─────────┐
    │   Data Volume    │
    │ ┌──────────────┐ │
    │ │  store.db    │ │
    │ └──────────────┘ │
    │ ┌──────────────┐ │
    │ │   images/    │ │
    │ └──────────────┘ │
    └──────────────────┘
```

### Key Decisions

- **Admin Auth**: HTTP Basic Auth initially
- **System Prompt**: Editable in config file (YAML)
- **Image Prompt**: Generated via Gemini from product description
- **Image Size**: 1K (1024x1024) square
- **Image Storage**: Save original PNG, serve converted JPG
- **Product Schema**: name, description, image_path, price, category, tags (JSON), rarity
- **HTMX Pattern**: Standard POST with loading states
- **Error Handling**: Human-in-the-loop (retry or discard)
- **Performance**: No pre-optimization; use threadpool if needed

---

## Step 3: Detailed Plan

### Finalized Tech Stack

**Backend**:
- Python 3.11+
- FastAPI (async framework)
- SQLAlchemy 2.x (ORM)
- SQLite (database)
- Uvicorn (ASGI server)
- `google-genai` (AI integration)
- Pillow (PNG→JPG conversion)

**Frontend**:
- Jinja2 (templating)
- HTMX (from CDN)
- Custom CSS (whimsical styling)

**Infrastructure**:
- Docker containerization
- Volume mount for `/data`
- Environment variables: `GEMINI_API_KEY`, `ADMIN_PASSWORD`

**Configuration**:
- YAML config file for system prompts (editable, mounted)

**Development Tools**:
- Ruff (linting/formatting)
- pytest (testing)

### Dependency Graph

```
Phase 1: Foundation (Parallel)
├── Project Structure & Config
├── Database Models
└── Gemini Client
    ↓
Phase 2: Core Services
└── Product Service
    ↓
Phase 3: Web Layer (Parallel)
├── Public Routes & Templates
└── Admin Routes & Templates
    ↓
Phase 4: Deployment
├── Docker & Compose
└── Documentation & Testing
```

### Sub-Projects

1. **Project Foundation & Configuration**
   - Project structure, config loading, logging
   - Dependencies: None

2. **Database Models & Setup**
   - SQLAlchemy models, database initialization
   - Dependencies: Sub-Project 1

3. **Gemini AI Client**
   - Text generation, image generation, error handling
   - Dependencies: Sub-Project 1

4. **Product Service Layer**
   - CRUD operations, AI orchestration, image conversion
   - Dependencies: Sub-Projects 2, 3

5. **Public Web Interface**
   - Storefront routes, templates, CSS
   - Dependencies: Sub-Project 4

6. **Admin Interface**
   - Admin routes, HTMX forms, authentication
   - Dependencies: Sub-Project 4

7. **Docker & Deployment**
   - Dockerfile, docker-compose, volume mounts
   - Dependencies: Sub-Projects 5, 6

8. **Documentation & Testing**
   - README, integration tests, troubleshooting
   - Dependencies: Sub-Project 7

### Execution Timeline Estimate

- Phase 1: 0.5 days
- Phase 2: 1 day
- Phase 3: 1.5 days
- Phase 4: 0.5 days
- **Total: 3.5 days**

---

## Step 4: Detailed Specifications

### Database Schema

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    price VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags JSON NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL
);
```

### API Interfaces

#### Configuration (`config.py`)
```python
class Config:
    @staticmethod
    def get_system_prompt() -> str
    @staticmethod
    def get_gemini_api_key() -> str
    @staticmethod
    def get_admin_password() -> str
    @staticmethod
    def get_data_dir() -> Path
    @staticmethod
    def get_image_dir() -> Path
```

#### Gemini Client (`services/gemini.py`)
```python
class GeminiClient:
    def generate_description(self, one_line_input: str) -> str
    def generate_image_prompt(self, description: str) -> str
    def generate_image(self, prompt: str, output_path: Path) -> Path
```

#### Product Service (`services/product.py`)
```python
class ProductService:
    def create_product_from_description(self, one_line: str) -> Product
    def get_all_products() -> List[Product]
    def get_product_by_id(self, product_id: int) -> Optional[Product]
```

#### Routes

**Public** (`routes/public.py`):
- `GET /` - Product list (HTML)
- `GET /product/{id}` - Product detail (HTML)

**Admin** (`routes/admin.py`):
- `GET /admin` - Admin product list (requires auth)
- `GET /admin/new` - Creation form (requires auth)
- `POST /admin/create` - Create product (HTMX, requires auth)

### Configuration File Structure

```yaml
# config.yaml
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

### Project Structure

```
magic-shop/
├── config.yaml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logger.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── product.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini.py
│   │   ├── product.py
│   │   └── image.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── public.py
│   │   └── admin.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── product.html
│   │   └── admin/
│   │       ├── base.html
│   │       ├── list.html
│   │       └── new.html
│   └── static/
│       └── css/
│           └── style.css
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_gemini.py
│   ├── test_product_service.py
│   └── test_integration.py
└── data/              # Volume mount (not in repo)
    ├── store.db
    └── images/
```

### Dependencies

```
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
jinja2>=3.1.2
python-multipart>=0.0.6
google-genai>=0.2.0
pillow>=10.1.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
pytest>=7.4.0
```

### Environment Variables

```bash
# .env.example
GEMINI_API_KEY=your_api_key_here
ADMIN_PASSWORD=your_secure_password
DATA_DIR=/data
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
COPY config.yaml .
RUN mkdir -p /data/images
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  magic-shop:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - DATA_DIR=/data
    volumes:
      - ./data:/data
      - ./config.yaml:/app/config.yaml
    restart: unless-stopped
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create project structure
- [ ] Set up configuration system (YAML + env vars)
- [ ] Create database models with SQLAlchemy
- [ ] Implement Gemini client wrapper

### Phase 2: Core Services
- [ ] Implement product service (CRUD + AI orchestration)
- [ ] Add image conversion (PNG→JPG)
- [ ] Add metadata extraction from descriptions

### Phase 3: Web Layer
- [ ] Create public routes and templates
- [ ] Style with whimsical CSS theme
- [ ] Create admin routes with HTTP Basic Auth
- [ ] Integrate HTMX for dynamic creation flow

### Phase 4: Deployment
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Create comprehensive README
- [ ] Write integration tests
- [ ] Test end-to-end workflow

---

## Testing Strategy

### Unit Tests
- Configuration loading
- Database models (CRUD operations)
- Gemini client (mocked API)
- Product service (mocked dependencies)
- Image conversion

### Integration Tests
- Full product creation workflow (with real API)
- Admin authentication
- Public site rendering
- Data persistence across container restarts

### Manual Tests
- Browse products on public site
- Create products via admin panel
- Verify images display correctly
- Test responsive layout
- Verify error handling (failed AI generation)

---

## Future Enhancements (Post-MVP)

- Product editing and deletion
- Search and filtering
- Product categories/tags navigation
- Pagination for large catalogs
- Image regeneration option
- Better admin UI with product preview
- Analytics (view counts)
- Export catalog as JSON
- Multiple admin users with roles
