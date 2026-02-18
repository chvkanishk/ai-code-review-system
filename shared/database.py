"""
Database models and connection
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import logging
from shared.config import settings

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class PRAnalysis(Base):
    """Table for storing PR analysis results"""
    __tablename__ = "pr_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    pr_title = Column(String(500))
    status = Column(String(50), default="pending")
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PRAnalysis(pr_number={self.pr_number}, status={self.status})>"


def init_db():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def health_check():
    """Check if database is accessible"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False