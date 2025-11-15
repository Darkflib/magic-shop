"""Admin routes for managing products in the magic shop."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import Config
from app.database import get_db
from app.logger import get_logger
from app.services.gemini import GeminiClient
from app.services.product import ProductCreationError, ProductService

logger = get_logger(__name__)

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify admin credentials using HTTP Basic Auth.

    Only the password is checked against ADMIN_PASSWORD environment variable.
    The username can be anything.

    Args:
        credentials: HTTP Basic Auth credentials

    Returns:
        The username (can be anything)

    Raises:
        HTTPException: 401 if password is invalid
    """
    try:
        admin_password = Config.get_admin_password()
    except Exception as e:
        logger.error("Failed to get admin password: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Server configuration error",
        )

    if credentials.password != admin_password:
        logger.warning("Failed admin login attempt with username: %s", credentials.username)
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info("Admin authenticated: %s", credentials.username)
    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def admin_product_list(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Depends(verify_admin)
):
    """Render the admin product list page.

    Shows all products in a table with admin controls.

    Args:
        request: FastAPI request object
        db: Database session dependency
        username: Authenticated username

    Returns:
        HTMLResponse with rendered admin/list.html template
    """
    logger.info("Admin %s accessing product list", username)

    # Initialize services (only need db for read operations)
    api_key = Config.get_gemini_api_key()
    system_prompts = Config.get_system_prompt()
    gemini_client = GeminiClient(api_key, system_prompts)
    image_dir = Config.get_image_dir()

    product_service = ProductService(db, gemini_client, image_dir)
    products = product_service.get_all_products()

    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "products": products,
            "username": username
        }
    )


@router.get("/new", response_class=HTMLResponse)
async def admin_new_product(
    request: Request,
    username: str = Depends(verify_admin)
):
    """Render the product creation form.

    Args:
        request: FastAPI request object
        username: Authenticated username

    Returns:
        HTMLResponse with rendered admin/new.html template
    """
    logger.info("Admin %s accessing new product form", username)

    return templates.TemplateResponse(
        "admin/new.html",
        {
            "request": request,
            "username": username
        }
    )


@router.post("/create", response_class=HTMLResponse)
async def admin_create_product(
    request: Request,
    description: str = Form(...),
    db: Session = Depends(get_db),
    username: str = Depends(verify_admin)
):
    """Create a new product from a one-line description.

    This endpoint is called via HTMX and returns HTML fragments
    to update the page dynamically. It handles the entire product
    creation pipeline which may take 10-30 seconds.

    Args:
        request: FastAPI request object
        description: One-line product description from form
        db: Database session dependency
        username: Authenticated username

    Returns:
        HTMLResponse with success or error HTML fragment
    """
    logger.info("Admin %s creating product from description: %s", username, description)

    # Return loading state immediately
    # Note: In a real-world scenario, you'd want to use BackgroundTasks
    # or a task queue for long-running operations. For this MVP,
    # we'll process synchronously and return the result.

    try:
        # Validate input
        if not description or not description.strip():
            logger.warning("Empty description provided")
            return HTMLResponse(
                content="""
                <div class="error">
                    ✗ Failed: Description cannot be empty
                    <button hx-get="/admin/new" hx-target="#result">Retry</button>
                </div>
                """,
                status_code=400
            )

        # Create the product (this may take 10-30 seconds)
        # Initialize services
        api_key = Config.get_gemini_api_key()
        system_prompts = Config.get_system_prompt()
        gemini_client = GeminiClient(api_key, system_prompts)
        image_dir = Config.get_image_dir()

        product_service = ProductService(db, gemini_client, image_dir)
        product = product_service.create_product_from_description(description.strip())

        logger.info("Product created successfully: ID=%d", product.id)

        # Return success fragment
        return HTMLResponse(
            content=f"""
            <div class="success">
                ✓ Product created! "{product.name}"
                <a href="/admin">View all</a>
                <a href="/admin/new">Create another</a>
            </div>
            """,
            status_code=200
        )

    except ProductCreationError as e:
        logger.error("Product creation failed: %s", str(e))
        error_message = str(e)
        # Clean up the error message for display
        if "Failed to create product: " in error_message:
            error_message = error_message.replace("Failed to create product: ", "")

        return HTMLResponse(
            content=f"""
            <div class="error">
                ✗ Failed: {error_message}
                <button hx-get="/admin/new" hx-target="#result">Retry</button>
            </div>
            """,
            status_code=500
        )

    except Exception as e:
        logger.error("Unexpected error during product creation: %s", str(e), exc_info=True)

        return HTMLResponse(
            content=f"""
            <div class="error">
                ✗ Failed: Unexpected error - {str(e)}
                <button hx-get="/admin/new" hx-target="#result">Retry</button>
            </div>
            """,
            status_code=500
        )
