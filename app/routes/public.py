"""Public-facing routes for the magic shop storefront."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.product import ProductService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    """Render the homepage with a grid of all products.

    Args:
        request: FastAPI request object
        db: Database session dependency

    Returns:
        HTMLResponse with rendered index.html template
    """
    products = ProductService.get_all_products(db)

    return templates.TemplateResponse(
        "index.html", {"request": request, "products": products}
    )


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request, product_id: int, db: Session = Depends(get_db)
):
    """Render the product detail page for a specific product.

    Args:
        request: FastAPI request object
        product_id: ID of the product to display
        db: Database session dependency

    Returns:
        HTMLResponse with rendered product.html template
        Returns 404 page if product not found
    """
    product = ProductService.get_product_by_id(db, product_id)

    if product is None:
        # Return a 404 page
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "product_id": product_id},
            status_code=404,
        )

    return templates.TemplateResponse(
        "product.html", {"request": request, "product": product}
    )
