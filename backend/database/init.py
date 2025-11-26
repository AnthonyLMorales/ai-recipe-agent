import logging

from database.connection import engine
from database.models import Base

logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
