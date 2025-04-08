"""
Database connection and session management for MCP persistence.

This module provides functions to initialize the database, create sessions,
and manage database connections. It supports multiple database backends
(SQLite for development, PostgreSQL for production).
"""

import os
import logging
from contextlib import contextmanager
from typing import Dict, Any, Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .models import Base

# Configure logging
logger = logging.getLogger(__name__)

# Global engine instance
_engine = None
_SessionLocal = None


def init_db(config: Dict[str, Any]) -> Engine:
    """
    Initialize the database connection.
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine, _SessionLocal
    
    db_config = config.get("database", {})
    db_type = db_config.get("type", "sqlite").lower()
    
    # Create database URL based on configuration
    if db_type == "sqlite":
        db_path = db_config.get("path", "mcp_data.db")
        db_url = f"sqlite:///{db_path}"
        logger.info(f"Using SQLite database at {db_path}")
    elif db_type == "postgresql":
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 5432)
        user = db_config.get("user", "postgres")
        password = db_config.get("password", "postgres")
        database = db_config.get("database", "mcp")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        logger.info(f"Using PostgreSQL database at {host}:{port}/{database}")
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    # Configure engine with appropriate settings
    connect_args = {}
    if db_type == "sqlite":
        connect_args["check_same_thread"] = False
    
    # Create engine with connection pooling
    _engine = create_engine(
        db_url,
        pool_size=db_config.get("pool_size", 5),
        max_overflow=db_config.get("max_overflow", 10),
        pool_timeout=db_config.get("pool_timeout", 30),
        pool_recycle=db_config.get("pool_recycle", 1800),  # Recycle connections after 30 minutes
        connect_args=connect_args,
        echo=db_config.get("echo", False),  # Set to True for SQL query logging
        poolclass=QueuePool
    )
    
    # Create session factory
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # Create tables if they don't exist
    if db_config.get("create_tables", True):
        logger.info("Creating database tables if they don't exist")
        Base.metadata.create_all(_engine)
    
    return _engine


def get_engine() -> Engine:
    """
    Get the SQLAlchemy engine instance.
    
    Returns:
        Engine: SQLAlchemy engine instance
    
    Raises:
        RuntimeError: If the database has not been initialized
    """
    global _engine
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
    
    Raises:
        RuntimeError: If the database has not been initialized
    """
    global _SessionLocal
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Session: SQLAlchemy session
    
    Example:
        with db_session() as session:
            session.add(some_object)
            session.commit()
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()