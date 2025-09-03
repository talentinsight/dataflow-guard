"""SQLAlchemy models for run store and persistence."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

Base = declarative_base()


class Run(Base):
    """Model for test run records."""
    __tablename__ = "runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    suite_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="running")  # running, completed, failed, error
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    bytes_scanned = Column(Integer, nullable=True)
    query_ids = Column(JSON, nullable=True)  # List of Snowflake query IDs
    environment = Column(String(50), nullable=False, default="dev")
    connection = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    tests = relationship("RunTest", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "suite_name": self.suite_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "bytes_scanned": self.bytes_scanned,
            "query_ids": self.query_ids,
            "environment": self.environment,
            "connection": self.connection,
            "error_message": self.error_message,
            "test_count": len(self.tests) if self.tests else 0,
            "artifact_count": len(self.artifacts) if self.artifacts else 0
        }


class RunTest(Base):
    """Model for individual test results within a run."""
    __tablename__ = "run_tests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # row_count, schema, null_check, etc.
    status = Column(String(50), nullable=False)  # pass, fail, error
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    observed = Column(JSON, nullable=True)  # Actual values observed
    expected = Column(JSON, nullable=True)  # Expected values
    query_id = Column(String(255), nullable=True)  # Snowflake query ID
    error_message = Column(Text, nullable=True)
    
    # Relationships
    run = relationship("Run", back_populates="tests")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "observed": self.observed,
            "expected": self.expected,
            "query_id": self.query_id,
            "error_message": self.error_message
        }


class Artifact(Base):
    """Model for run artifacts stored in MinIO."""
    __tablename__ = "artifacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    kind = Column(String(100), nullable=False)  # report, logs, data_sample, etc.
    path = Column(String(500), nullable=False)  # S3/MinIO path
    url = Column(String(500), nullable=True)  # Pre-signed URL
    size_bytes = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For pre-signed URLs
    
    # Relationships
    run = relationship("Run", back_populates="artifacts")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "kind": self.kind,
            "path": self.path,
            "url": self.url,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global database manager instance (will be initialized in main.py)
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager


def init_database(database_url: str) -> DatabaseManager:
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager
