"""Tests for the ProductService with AI-enhanced creation."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Product
from app.services.gemini import GeminiAPIError, GeminiClient
from app.services.image import ImageConversionError
from app.services.product import ProductCreationError, ProductService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_gemini_client():
    """Create a mock GeminiClient for testing."""
    client = Mock(spec=GeminiClient)
    client.text_model = "gemini-2.0-flash-exp"
    client.image_model = "gemini-2.5-flash-image"

    # Mock the nested client.models.generate_content
    client.client = Mock()
    client.client.models = Mock()

    return client


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory for image storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def product_service(db_session, mock_gemini_client, temp_image_dir):
    """Create a ProductService instance for testing."""
    return ProductService(db_session, mock_gemini_client, temp_image_dir)


class TestProductServiceInitialization:
    """Test ProductService initialization."""

    def test_init_creates_image_directory(self, db_session, mock_gemini_client):
        """Test that initialization creates the image directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_dir = Path(tmpdir) / "images" / "products"
            assert not image_dir.exists()

            service = ProductService(db_session, mock_gemini_client, image_dir)

            assert image_dir.exists()
            assert service.db == db_session
            assert service.gemini_client == mock_gemini_client
            assert service.image_dir == image_dir

    def test_init_with_existing_directory(self, db_session, mock_gemini_client, temp_image_dir):
        """Test initialization with an existing directory."""
        service = ProductService(db_session, mock_gemini_client, temp_image_dir)

        assert service.image_dir == temp_image_dir
        assert temp_image_dir.exists()


class TestProductCreation:
    """Test product creation workflow."""

    def test_create_product_from_description_success(self, product_service, mock_gemini_client, temp_image_dir):
        """Test successful product creation from description."""
        # Setup mock responses
        mock_description = "A magnificent sword forged in dragon fire, capable of cutting through any material."
        mock_image_prompt = "A glowing magical sword with dragon motifs, fantasy art style"

        mock_gemini_client.generate_description.return_value = mock_description
        mock_gemini_client.generate_image_prompt.return_value = mock_image_prompt

        # Mock metadata extraction
        mock_metadata_response = Mock()
        mock_metadata_response.text = json.dumps({
            "name": "Dragon Fire Sword",
            "category": "Weapons",
            "tags": ["dragon", "fire", "sword", "legendary"],
            "rarity": "Legendary",
            "price": "10000 Gold Coins"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_metadata_response

        # Mock image generation - create a real PNG file
        def mock_generate_image(prompt, output_path):
            img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
            img.save(output_path, 'PNG')
            return output_path

        mock_gemini_client.generate_image.side_effect = mock_generate_image

        # Create product
        product = product_service.create_product_from_description("a magical sword")

        # Verify product was created correctly
        assert product.id is not None
        assert product.name == "Dragon Fire Sword"
        assert product.description == mock_description
        assert product.category == "Weapons"
        assert product.tags == ["dragon", "fire", "sword", "legendary"]
        assert product.rarity == "Legendary"
        assert product.price == "10000 Gold Coins"

        # Verify image paths
        assert product.image_path.endswith('.jpg')
        jpg_path = Path(product.image_path)
        assert jpg_path.exists()

        # Verify PNG was also created
        png_path = jpg_path.with_suffix('.png')
        assert png_path.exists()

        # Verify Gemini was called correctly
        mock_gemini_client.generate_description.assert_called_once_with("a magical sword")
        mock_gemini_client.generate_image_prompt.assert_called_once_with(mock_description)
        assert mock_gemini_client.generate_image.called

    def test_create_product_gemini_description_fails(self, product_service, mock_gemini_client):
        """Test handling of Gemini API failure during description generation."""
        mock_gemini_client.generate_description.side_effect = GeminiAPIError("API quota exceeded")

        with pytest.raises(ProductCreationError, match="AI generation failed"):
            product_service.create_product_from_description("test product")

        # Verify no product was created
        products = product_service.get_all_products()
        assert len(products) == 0

    def test_create_product_gemini_image_fails(self, product_service, mock_gemini_client):
        """Test handling of Gemini API failure during image generation."""
        mock_description = "Test description"
        mock_gemini_client.generate_description.return_value = mock_description
        mock_gemini_client.generate_image_prompt.return_value = "test prompt"

        # Mock metadata extraction
        mock_metadata_response = Mock()
        mock_metadata_response.text = json.dumps({
            "name": "Test Item",
            "category": "Artifacts",
            "tags": ["test", "item"],
            "rarity": "Common",
            "price": "10 Gold"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_metadata_response

        mock_gemini_client.generate_image.side_effect = GeminiAPIError("Image generation failed")

        with pytest.raises(ProductCreationError, match="AI generation failed"):
            product_service.create_product_from_description("test product")

        # Verify transaction was rolled back
        products = product_service.get_all_products()
        assert len(products) == 0

    def test_create_product_image_conversion_fails(self, product_service, mock_gemini_client, temp_image_dir):
        """Test handling of image conversion failure."""
        mock_description = "Test description"
        mock_gemini_client.generate_description.return_value = mock_description
        mock_gemini_client.generate_image_prompt.return_value = "test prompt"

        # Mock metadata extraction
        mock_metadata_response = Mock()
        mock_metadata_response.text = json.dumps({
            "name": "Test Item",
            "category": "Artifacts",
            "tags": ["test", "item"],
            "rarity": "Common",
            "price": "10 Gold"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_metadata_response

        # Mock image generation to create invalid PNG
        def mock_generate_image(prompt, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'invalid image data')
            return output_path

        mock_gemini_client.generate_image.side_effect = mock_generate_image

        with pytest.raises(ProductCreationError, match="Image conversion failed"):
            product_service.create_product_from_description("test product")

        # Verify transaction was rolled back
        products = product_service.get_all_products()
        assert len(products) == 0

    def test_create_product_with_minimal_tags(self, product_service, mock_gemini_client, temp_image_dir):
        """Test product creation when metadata has less than 2 tags."""
        mock_description = "A simple potion"
        mock_gemini_client.generate_description.return_value = mock_description
        mock_gemini_client.generate_image_prompt.return_value = "potion image"

        # Mock metadata extraction with only 1 tag
        mock_metadata_response = Mock()
        mock_metadata_response.text = json.dumps({
            "name": "Simple Potion",
            "category": "Potions",
            "tags": ["healing"],  # Only 1 tag
            "rarity": "Common",
            "price": "5 Gold"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_metadata_response

        # Mock image generation
        def mock_generate_image(prompt, output_path):
            img = Image.new('RGB', (50, 50), color=(0, 255, 0))
            img.save(output_path, 'PNG')
            return output_path

        mock_gemini_client.generate_image.side_effect = mock_generate_image

        product = product_service.create_product_from_description("a healing potion")

        # Should have at least 2 tags (original + 'Magical' added)
        assert len(product.tags) >= 2
        assert "healing" in product.tags


class TestMetadataExtraction:
    """Test metadata extraction from descriptions."""

    def test_extract_metadata_success(self, product_service, mock_gemini_client):
        """Test successful metadata extraction."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "name": "Staff of Power",
            "category": "Wands",
            "tags": ["magic", "staff", "power"],
            "rarity": "Epic",
            "price": "5000 Gold Coins"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        metadata = product_service._extract_metadata("A powerful magical staff")

        assert metadata['name'] == "Staff of Power"
        assert metadata['category'] == "Wands"
        assert metadata['tags'] == ["magic", "staff", "power"]
        assert metadata['rarity'] == "Epic"
        assert metadata['price'] == "5000 Gold Coins"

    def test_extract_metadata_with_markdown_code_blocks(self, product_service, mock_gemini_client):
        """Test metadata extraction when response includes markdown code blocks."""
        mock_response = Mock()
        mock_response.text = """```json
{
  "name": "Ring of Invisibility",
  "category": "Rings",
  "tags": ["invisibility", "stealth", "magic"],
  "rarity": "Rare",
  "price": "3000 Gold"
}
```"""
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        metadata = product_service._extract_metadata("An invisibility ring")

        assert metadata['name'] == "Ring of Invisibility"
        assert metadata['category'] == "Rings"

    def test_extract_metadata_invalid_json(self, product_service, mock_gemini_client):
        """Test error handling for invalid JSON in metadata extraction."""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ProductCreationError, match="Failed to parse metadata JSON"):
            product_service._extract_metadata("test description")

    def test_extract_metadata_missing_required_field(self, product_service, mock_gemini_client):
        """Test error handling when required fields are missing."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "name": "Incomplete Item",
            "category": "Artifacts"
            # Missing tags, rarity, price
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ProductCreationError, match="Missing required field"):
            product_service._extract_metadata("test description")

    def test_extract_metadata_tags_not_list(self, product_service, mock_gemini_client):
        """Test error handling when tags is not a list."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "name": "Bad Tags Item",
            "category": "Artifacts",
            "tags": "should be a list",
            "rarity": "Common",
            "price": "10 Gold"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ProductCreationError, match="Tags must be a list"):
            product_service._extract_metadata("test description")

    def test_extract_metadata_empty_response(self, product_service, mock_gemini_client):
        """Test error handling for empty Gemini response."""
        mock_response = Mock()
        mock_response.text = None
        mock_gemini_client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ProductCreationError, match="Empty response from Gemini"):
            product_service._extract_metadata("test description")


class TestProductRetrieval:
    """Test product retrieval methods."""

    def test_get_all_products_empty(self, product_service):
        """Test retrieving products when database is empty."""
        products = product_service.get_all_products()
        assert products == []

    def test_get_all_products_ordered_by_created_at(self, product_service, db_session):
        """Test that products are returned ordered by created_at DESC."""
        # Create products with different timestamps
        product1 = Product(
            name="Old Product",
            description="First product",
            image_path="/path/1.jpg",
            price="100 Gold",
            category="Weapons",
            tags=["old", "test"],
            rarity="Common"
        )
        db_session.add(product1)
        db_session.flush()

        # Ensure different timestamps
        import time
        time.sleep(0.01)

        product2 = Product(
            name="New Product",
            description="Second product",
            image_path="/path/2.jpg",
            price="200 Gold",
            category="Potions",
            tags=["new", "test"],
            rarity="Rare"
        )
        db_session.add(product2)
        db_session.commit()

        products = product_service.get_all_products()

        assert len(products) == 2
        # Newer product should be first
        assert products[0].name == "New Product"
        assert products[1].name == "Old Product"

    def test_get_product_by_id_found(self, product_service, db_session):
        """Test retrieving a product by ID when it exists."""
        product = Product(
            name="Test Product",
            description="Description",
            image_path="/path/test.jpg",
            price="50 Gold",
            category="Artifacts",
            tags=["test"],
            rarity="Uncommon"
        )
        db_session.add(product)
        db_session.commit()

        found_product = product_service.get_product_by_id(product.id)

        assert found_product is not None
        assert found_product.id == product.id
        assert found_product.name == "Test Product"

    def test_get_product_by_id_not_found(self, product_service):
        """Test retrieving a product by ID when it doesn't exist."""
        product = product_service.get_product_by_id(999)
        assert product is None

    def test_get_product_by_id_multiple_products(self, product_service, db_session):
        """Test that get_product_by_id returns the correct product when multiple exist."""
        product1 = Product(
            name="Product 1",
            description="First",
            image_path="/path/1.jpg",
            price="10 Gold",
            category="Weapons",
            tags=["test"],
            rarity="Common"
        )
        product2 = Product(
            name="Product 2",
            description="Second",
            image_path="/path/2.jpg",
            price="20 Gold",
            category="Armor",
            tags=["test"],
            rarity="Rare"
        )
        db_session.add_all([product1, product2])
        db_session.commit()

        found = product_service.get_product_by_id(product2.id)
        assert found.name == "Product 2"


class TestProductServiceErrorHandling:
    """Test error handling in ProductService."""

    def test_get_all_products_database_error(self, product_service):
        """Test error handling when database query fails."""
        # Mock the database query to raise an exception
        with patch.object(product_service.db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database connection error")

            with pytest.raises(ProductCreationError, match="Failed to retrieve products"):
                product_service.get_all_products()

    def test_get_product_by_id_database_error(self, product_service):
        """Test error handling when database query fails for get_by_id."""
        # Mock the database query to raise an exception
        with patch.object(product_service.db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database connection error")

            with pytest.raises(ProductCreationError, match="Failed to retrieve product"):
                product_service.get_product_by_id(1)


class TestProductCreationWorkflow:
    """Integration tests for the full product creation workflow."""

    def test_full_workflow_with_all_steps(self, product_service, mock_gemini_client, temp_image_dir):
        """Test the complete product creation workflow end-to-end."""
        one_line = "A mystical amulet that grants visions of the future"

        # Setup all mocks
        mock_description = """The Amulet of Foresight is an ancient artifact crafted by the Oracle of Delphi.
        This mystical pendant contains a swirling vortex of ethereal energy that grants its wearer
        glimpses into possible futures. The amulet is set in platinum and adorned with a large
        sapphire that glows with an inner light."""

        mock_image_prompt = "A mystical amulet with glowing sapphire, ethereal energy swirls, platinum setting, oracle artifact, magical jewelry"

        mock_gemini_client.generate_description.return_value = mock_description
        mock_gemini_client.generate_image_prompt.return_value = mock_image_prompt

        # Mock metadata extraction
        mock_metadata_response = Mock()
        mock_metadata_response.text = json.dumps({
            "name": "Amulet of Foresight",
            "category": "Amulets",
            "tags": ["oracle", "vision", "future", "mystical"],
            "rarity": "Legendary",
            "price": "15000 Gold Coins"
        })
        mock_gemini_client.client.models.generate_content.return_value = mock_metadata_response

        # Mock image generation
        def mock_generate_image(prompt, output_path):
            img = Image.new('RGBA', (256, 256), color=(0, 100, 200, 255))
            img.save(output_path, 'PNG')
            return output_path

        mock_gemini_client.generate_image.side_effect = mock_generate_image

        # Execute the full workflow
        product = product_service.create_product_from_description(one_line)

        # Verify all steps completed successfully
        assert product.id == 1
        assert product.name == "Amulet of Foresight"
        assert product.description == mock_description
        assert product.category == "Amulets"
        assert "oracle" in product.tags
        assert product.rarity == "Legendary"
        assert product.price == "15000 Gold Coins"

        # Verify images were created
        jpg_path = Path(product.image_path)
        assert jpg_path.exists()
        assert jpg_path.suffix == '.jpg'

        png_path = jpg_path.with_suffix('.png')
        assert png_path.exists()

        # Verify filename includes product ID
        assert f"{product.id}_" in jpg_path.name

        # Verify the product can be retrieved
        retrieved = product_service.get_product_by_id(product.id)
        assert retrieved.name == "Amulet of Foresight"
