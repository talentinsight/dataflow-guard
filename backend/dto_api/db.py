"""Database configuration and utilities."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    """Get database URL from environment with fallback to SQLite for development.
    
    Returns:
        Database URL string. Defaults to SQLite if DATABASE_URL not set.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Default to SQLite for development
        database_url = "sqlite:///./dto.db"
    return database_url


def get_engine():
    """Create SQLAlchemy engine with appropriate configuration.
    
    Returns:
        SQLAlchemy engine configured for the database type.
    """
    url = get_database_url()
    
    # Base engine configuration
    engine_kwargs = {}
    
    # PostgreSQL-specific pool options
    if url.startswith("postgresql"):
        engine_kwargs.update({
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 5,
            "max_overflow": 10,
        })
    # SQLite-specific configuration
    elif url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
        })
    
    return create_engine(url, **engine_kwargs)


# Session factory - will be configured when engine is created
SessionLocal = sessionmaker(autocommit=False, autoflush=False, future=True)

# Global engine instance
_engine = None

def get_session_local():
    """Get configured SessionLocal factory."""
    global _engine
    if _engine is None:
        _engine = get_engine()
        SessionLocal.configure(bind=_engine)
    return SessionLocal
