"""Database setup and session management for the magic shop."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Config
from app.models.product import Base


def get_engine() -> Engine:
    """Create and return a SQLAlchemy engine for the SQLite database.

    The database file is created in the data directory as store.db.
    Creates the data directory if it doesn't exist.

    Returns:
        SQLAlchemy Engine instance connected to the SQLite database.
    """
    data_dir = Config.get_data_dir()

    # Create data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "store.db"

    # Create the database URL
    # Use forward slashes for SQLite URL, even on Windows
    db_url = f"sqlite:///{db_path.as_posix()}"

    # Create engine with echo=False for production
    # Use check_same_thread=False for SQLite to allow usage across threads
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    return engine


def init_db() -> None:
    """Initialize the database by creating all tables.

    This function creates all tables defined in the Base metadata.
    It's safe to call multiple times - existing tables won't be modified.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    This is a generator function that yields a SQLAlchemy Session.
    It ensures the session is properly closed after use.

    Yields:
        SQLAlchemy Session instance.

    Example:
        >>> for session in get_db():
        ...     products = session.query(Product).all()
        ...     # session is automatically closed after the loop
    """
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
