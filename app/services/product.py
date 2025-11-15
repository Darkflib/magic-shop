"""Product service layer for managing magical items with AI-enhanced creation."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.logger import get_logger
from app.models import Product
from app.services.gemini import GeminiClient, GeminiAPIError
from app.services.image import convert_png_to_jpg, ImageConversionError


logger = get_logger(__name__)


class ProductCreationError(Exception):
    """Exception raised when product creation fails."""
    pass


class ProductService:
    """Service for managing product operations with AI-enhanced creation.

    This service orchestrates the complete product creation workflow:
    1. Generate detailed description from one-line input
    2. Generate image prompt from description
    3. Generate and save product image (PNG)
    4. Convert PNG to JPG for serving
    5. Extract metadata (name, category, tags, rarity, price)
    6. Create database record

    Attributes:
        db: SQLAlchemy database session
        gemini_client: Client for Gemini AI operations
        image_dir: Directory where product images are stored
    """

    def __init__(self, db: Session, gemini_client: GeminiClient, image_dir: Path):
        """Initialize the ProductService.

        Args:
            db: SQLAlchemy database session
            gemini_client: Initialized GeminiClient for AI operations
            image_dir: Path to directory for storing product images
        """
        self.db = db
        self.gemini_client = gemini_client
        self.image_dir = image_dir

        # Ensure image directory exists
        self.image_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ProductService initialized with image_dir: %s", self.image_dir)

    def create_product_from_description(self, one_line: str) -> Product:
        """Create a complete product from a one-line description using AI.

        This method orchestrates the entire product creation workflow:
        - Generates a full product description
        - Creates an image prompt and generates the image
        - Converts the image to JPG format
        - Extracts structured metadata
        - Saves everything to the database

        Args:
            one_line: Brief one-line description of the product idea

        Returns:
            The created Product object with all fields populated

        Raises:
            ProductCreationError: If any step of the creation process fails
        """
        logger.info("Creating product from description: %s", one_line)

        try:
            # Step 1: Generate full description
            logger.info("Step 1: Generating full description")
            description = self.gemini_client.generate_description(one_line)
            logger.debug("Generated description: %s", description[:100])

            # Step 2: Generate image prompt
            logger.info("Step 2: Generating image prompt")
            image_prompt = self.gemini_client.generate_image_prompt(description)
            logger.debug("Generated image prompt: %s", image_prompt[:100])

            # Step 3: Extract metadata before creating the product record
            # We need this to get the name and other fields
            logger.info("Step 3: Extracting metadata from description")
            metadata = self._extract_metadata(description)
            logger.debug("Extracted metadata: %s", metadata)

            # Step 4: Create a temporary product record to get an ID for filenames
            # We'll update it with the image path later
            product = Product(
                name=metadata['name'],
                description=description,
                image_path='',  # Temporary, will update after image generation
                price=metadata['price'],
                category=metadata['category'],
                tags=metadata['tags'],
                rarity=metadata['rarity']
            )
            self.db.add(product)
            self.db.flush()  # Get the ID without committing
            logger.info("Created temporary product record with ID: %d", product.id)

            # Step 5: Generate image with product ID in filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            png_filename = f"{product.id}_{timestamp}.png"
            jpg_filename = f"{product.id}_{timestamp}.jpg"
            png_path = self.image_dir / png_filename
            jpg_path = self.image_dir / jpg_filename

            logger.info("Step 4: Generating product image")
            self.gemini_client.generate_image(image_prompt, png_path)
            logger.info("Image generated: %s", png_path)

            # Step 6: Convert PNG to JPG
            logger.info("Step 5: Converting PNG to JPG")
            convert_png_to_jpg(png_path, jpg_path, quality=85)
            logger.info("Image converted to JPG: %s", jpg_path)

            # Step 7: Update product with image path (store web-accessible path)
            # Store path relative to web root: /images/filename.jpg
            product.image_path = f"/images/{jpg_filename}"
            logger.debug("Updated product image_path: %s", product.image_path)

            # Step 8: Commit the transaction
            self.db.commit()
            self.db.refresh(product)
            logger.info("Successfully created product with ID: %d", product.id)

            return product

        except GeminiAPIError as e:
            self.db.rollback()
            error_msg = f"AI generation failed: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

        except ImageConversionError as e:
            self.db.rollback()
            error_msg = f"Image conversion failed: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

        except Exception as e:
            self.db.rollback()
            error_msg = f"Product creation failed: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

    def get_all_products(self) -> List[Product]:
        """Retrieve all products ordered by creation date (newest first).

        Returns:
            List of Product objects ordered by created_at DESC
        """
        logger.info("Retrieving all products")
        try:
            products = self.db.query(Product).order_by(Product.created_at.desc()).all()
            logger.info("Retrieved %d products", len(products))
            return products
        except Exception as e:
            error_msg = f"Failed to retrieve products: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Retrieve a product by its ID.

        Args:
            product_id: The ID of the product to retrieve

        Returns:
            Product object if found, None otherwise
        """
        logger.info("Retrieving product with ID: %d", product_id)
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                logger.info("Found product: %s", product.name)
            else:
                logger.info("Product not found with ID: %d", product_id)
            return product
        except Exception as e:
            error_msg = f"Failed to retrieve product {product_id}: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

    def _extract_metadata(self, description: str) -> dict:
        """Extract structured metadata from a product description using AI.

        Uses Gemini to analyze the description and extract:
        - name: Product name
        - category: Product category (e.g., "Weapons", "Potions", "Artifacts")
        - tags: List of 2-5 relevant tags
        - rarity: Rarity level (Legendary/Epic/Rare/Uncommon)
        - price: Price string (e.g., "500 Gold Coins")

        Args:
            description: The product description to analyze

        Returns:
            Dictionary with metadata fields

        Raises:
            ProductCreationError: If metadata extraction fails
        """
        logger.info("Extracting metadata from description")

        metadata_prompt = f"""Analyze this magical product description and extract structured metadata.
Return ONLY a valid JSON object with these exact fields (no markdown, no code blocks, just the JSON):

{{
  "name": "A concise product name (max 200 chars)",
  "category": "One of: Weapons, Potions, Artifacts, Armor, Scrolls, Wands, Rings, Amulets, Books, Ingredients",
  "tags": ["2-5 relevant tags as strings"],
  "rarity": "One of: Legendary, Epic, Rare, Uncommon, Common",
  "price": "Price with currency (e.g., '500 Gold Coins', '1000 Silver Pieces')"
}}

Description to analyze:
{description}

Return only the JSON object:"""

        try:
            response = self.gemini_client.client.models.generate_content(
                model=self.gemini_client.text_model,
                contents=metadata_prompt
            )

            if not response or not response.text:
                raise ProductCreationError("Empty response from Gemini for metadata extraction")

            # Clean up the response - remove markdown code blocks if present
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Remove code block markers
                lines = response_text.split('\n')
                # Remove first line (```json or ```) and last line (```)
                response_text = '\n'.join(lines[1:-1])

            # Parse JSON response
            metadata = json.loads(response_text)
            logger.debug("Parsed metadata: %s", metadata)

            # Validate required fields
            required_fields = ['name', 'category', 'tags', 'rarity', 'price']
            for field in required_fields:
                if field not in metadata:
                    raise ProductCreationError(f"Missing required field in metadata: {field}")

            # Validate tags is a list
            if not isinstance(metadata['tags'], list):
                raise ProductCreationError("Tags must be a list")

            # Ensure we have at least 2 tags and at most 5
            if len(metadata['tags']) < 2:
                metadata['tags'].append('Magical')  # Add a default tag if needed
            metadata['tags'] = metadata['tags'][:5]  # Limit to 5 tags

            logger.info("Successfully extracted metadata: name=%s, category=%s, rarity=%s",
                       metadata['name'], metadata['category'], metadata['rarity'])

            return metadata

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse metadata JSON: {str(e)}"
            logger.error(error_msg)
            logger.error("Response text was: %s", response_text if 'response_text' in locals() else "N/A")
            raise ProductCreationError(error_msg) from e

        except GeminiAPIError as e:
            error_msg = f"Gemini API error during metadata extraction: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to extract metadata: {str(e)}"
            logger.error(error_msg)
            raise ProductCreationError(error_msg) from e
