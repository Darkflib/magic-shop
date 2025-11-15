"""Tests for database models."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Product


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing.

    Yields:
        SQLAlchemy Session instance connected to in-memory database.
    """
    # Create in-memory SQLite engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(engine)


def test_create_product_with_all_fields(in_memory_db: Session):
    """Test creating a product with all fields populated."""
    # Arrange
    product = Product(
        name="Dragon's Eye Amulet",
        description="A mystical amulet containing the eye of an ancient dragon. "
        "Grants the wearer incredible foresight and protection against fire.",
        image_path="/data/images/dragons-eye-amulet.jpg",
        price="500 Gold Coins",
        category="Amulets",
        tags=["magic", "dragon", "protection", "legendary"],
        rarity="Legendary",
    )

    # Act
    in_memory_db.add(product)
    in_memory_db.commit()
    in_memory_db.refresh(product)

    # Assert
    assert product.id is not None
    assert product.name == "Dragon's Eye Amulet"
    assert "ancient dragon" in product.description
    assert product.image_path == "/data/images/dragons-eye-amulet.jpg"
    assert product.price == "500 Gold Coins"
    assert product.category == "Amulets"
    assert product.tags == ["magic", "dragon", "protection", "legendary"]
    assert product.rarity == "Legendary"
    assert isinstance(product.created_at, datetime)


def test_product_json_tags_field(in_memory_db: Session):
    """Test that tags field properly stores and retrieves JSON array."""
    # Arrange
    tags_list = ["enchanted", "rare", "mystical", "powerful"]
    product = Product(
        name="Enchanted Staff",
        description="A powerful staff imbued with ancient magic.",
        image_path="/data/images/enchanted-staff.jpg",
        price="300 Gold Coins",
        category="Weapons",
        tags=tags_list,
        rarity="Rare",
    )

    # Act
    in_memory_db.add(product)
    in_memory_db.commit()
    in_memory_db.refresh(product)

    # Assert - tags should be stored and retrieved as a list
    assert isinstance(product.tags, list)
    assert product.tags == tags_list
    assert len(product.tags) == 4
    assert "enchanted" in product.tags
    assert "powerful" in product.tags


def test_product_empty_tags(in_memory_db: Session):
    """Test that product can have empty tags list."""
    # Arrange
    product = Product(
        name="Mystery Box",
        description="A mysterious box with unknown contents.",
        image_path="/data/images/mystery-box.jpg",
        price="100 Gold Coins",
        category="Miscellaneous",
        tags=[],
        rarity="Common",
    )

    # Act
    in_memory_db.add(product)
    in_memory_db.commit()
    in_memory_db.refresh(product)

    # Assert
    assert product.tags == []
    assert isinstance(product.tags, list)


def test_database_persistence(in_memory_db: Session):
    """Test that products persist correctly in the database."""
    # Arrange - Create multiple products
    product1 = Product(
        name="Phoenix Feather",
        description="A feather from a mythical phoenix.",
        image_path="/data/images/phoenix-feather.jpg",
        price="1000 Gold Coins",
        category="Materials",
        tags=["phoenix", "rare", "rebirth"],
        rarity="Legendary",
    )
    product2 = Product(
        name="Healing Potion",
        description="Restores health instantly.",
        image_path="/data/images/healing-potion.jpg",
        price="50 Gold Coins",
        category="Potions",
        tags=["healing", "potion", "consumable"],
        rarity="Common",
    )

    # Act - Add products to database
    in_memory_db.add(product1)
    in_memory_db.add(product2)
    in_memory_db.commit()

    # Query products back
    all_products = in_memory_db.query(Product).all()
    phoenix_feather = (
        in_memory_db.query(Product).filter(Product.name == "Phoenix Feather").first()
    )
    healing_potion = (
        in_memory_db.query(Product).filter(Product.name == "Healing Potion").first()
    )

    # Assert - Products are persisted correctly
    assert len(all_products) == 2
    assert phoenix_feather is not None
    assert phoenix_feather.rarity == "Legendary"
    assert phoenix_feather.price == "1000 Gold Coins"
    assert healing_potion is not None
    assert healing_potion.rarity == "Common"
    assert healing_potion.category == "Potions"


def test_product_created_at_auto_set(in_memory_db: Session):
    """Test that created_at is automatically set to current UTC time."""
    # Arrange
    before_creation = datetime.utcnow()
    product = Product(
        name="Time Stone",
        description="A stone that bends time itself.",
        image_path="/data/images/time-stone.jpg",
        price="2000 Gold Coins",
        category="Artifacts",
        tags=["time", "artifact", "legendary"],
        rarity="Legendary",
    )

    # Act
    in_memory_db.add(product)
    in_memory_db.commit()
    in_memory_db.refresh(product)
    after_creation = datetime.utcnow()

    # Assert
    assert product.created_at is not None
    assert isinstance(product.created_at, datetime)
    # The created_at should be between before and after (within a reasonable margin)
    assert before_creation <= product.created_at <= after_creation


def test_product_repr(in_memory_db: Session):
    """Test the __repr__ method of Product."""
    # Arrange
    product = Product(
        name="Magic Wand",
        description="A basic magic wand for beginners.",
        image_path="/data/images/magic-wand.jpg",
        price="25 Gold Coins",
        category="Wands",
        tags=["magic", "beginner"],
        rarity="Common",
    )

    # Act
    in_memory_db.add(product)
    in_memory_db.commit()
    in_memory_db.refresh(product)
    repr_string = repr(product)

    # Assert
    assert "Product(" in repr_string
    assert "name='Magic Wand'" in repr_string
    assert "category='Wands'" in repr_string
    assert "rarity='Common'" in repr_string
    assert f"id={product.id}" in repr_string


def test_query_by_category(in_memory_db: Session):
    """Test querying products by category."""
    # Arrange - Create products in different categories
    potion1 = Product(
        name="Mana Potion",
        description="Restores magical energy.",
        image_path="/data/images/mana-potion.jpg",
        price="75 Gold Coins",
        category="Potions",
        tags=["mana", "potion"],
        rarity="Common",
    )
    potion2 = Product(
        name="Strength Potion",
        description="Increases physical strength.",
        image_path="/data/images/strength-potion.jpg",
        price="100 Gold Coins",
        category="Potions",
        tags=["strength", "potion"],
        rarity="Uncommon",
    )
    weapon = Product(
        name="Mystic Sword",
        description="A sword with magical properties.",
        image_path="/data/images/mystic-sword.jpg",
        price="500 Gold Coins",
        category="Weapons",
        tags=["sword", "weapon"],
        rarity="Rare",
    )

    # Act
    in_memory_db.add_all([potion1, potion2, weapon])
    in_memory_db.commit()

    # Query potions
    potions = in_memory_db.query(Product).filter(Product.category == "Potions").all()
    weapons = in_memory_db.query(Product).filter(Product.category == "Weapons").all()

    # Assert
    assert len(potions) == 2
    assert all(p.category == "Potions" for p in potions)
    assert len(weapons) == 1
    assert weapons[0].name == "Mystic Sword"


def test_query_by_rarity(in_memory_db: Session):
    """Test querying products by rarity level."""
    # Arrange
    common_item = Product(
        name="Wooden Staff",
        description="A simple wooden staff.",
        image_path="/data/images/wooden-staff.jpg",
        price="10 Gold Coins",
        category="Weapons",
        tags=["staff", "basic"],
        rarity="Common",
    )
    legendary_item = Product(
        name="Crown of Kings",
        description="The crown worn by ancient kings.",
        image_path="/data/images/crown-of-kings.jpg",
        price="10000 Gold Coins",
        category="Artifacts",
        tags=["crown", "artifact", "royal"],
        rarity="Legendary",
    )

    # Act
    in_memory_db.add_all([common_item, legendary_item])
    in_memory_db.commit()

    # Query by rarity
    legendary_items = (
        in_memory_db.query(Product).filter(Product.rarity == "Legendary").all()
    )

    # Assert
    assert len(legendary_items) == 1
    assert legendary_items[0].name == "Crown of Kings"
    assert legendary_items[0].price == "10000 Gold Coins"
