from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
import logging

# Configure logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

SQLALCHEMY_DATABASE_URL = f"sqlite:///./{settings.DATABASE_NAME}"

# Create engine with connection pooling optimizations
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_size=10,            # Number of connections to maintain
    max_overflow=20,         # Additional connections beyond pool_size
    echo=settings.DEBUG      # Log SQL statements in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database dependency for FastAPI with proper session management"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
