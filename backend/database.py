from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leveling_guide.db")

# Handle different database backends
if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_size=5,         # Number of connections to keep open
        max_overflow=10,     # Allow up to 10 extra connections
    )
elif "sqlite" in DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # Wait up to 30 seconds for lock
        }
    )
    
    # Enable WAL mode for better concurrent access (SQLite only)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds in milliseconds
        cursor.close()
else:
    # Generic fallback
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from models import Company, User, Nudge, Role, Level, Competency, Definition, Example  # noqa
    Base.metadata.create_all(bind=engine)
