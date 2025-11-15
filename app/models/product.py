"""SQLAlchemy models for the magic shop."""

from datetime import datetime
from typing import List

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Product(Base):
    """Product model representing a magical item in the shop.

    Attributes:
        id: Primary key
        name: Product name (max 200 chars)
        description: Full product description (text)
        image_path: Path to product image (max 500 chars)
        price: Product price as string (e.g., "500 Gold Coins", max 100 chars)
        category: Product category (max 100 chars)
        tags: List of tags stored as JSON array
        rarity: Product rarity level (e.g., "Legendary", max 50 chars)
        created_at: Timestamp when product was created (UTC)
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    rarity: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        """Return a string representation of the Product."""
        return (
            f"Product(id={self.id!r}, name={self.name!r}, "
            f"category={self.category!r}, rarity={self.rarity!r})"
        )
