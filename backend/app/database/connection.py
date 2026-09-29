import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from backend.app.config import settings

logger = logging.getLogger("email_agent.database")

# Normalize URL for SQLAlchemy with psycopg3
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Connection engine with Neon-friendly connection pooling
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "connect_timeout": 15
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> dict:
    """Test database connection and return server version and current DB."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user, version();")).fetchone()
            return {
                "status": "connected",
                "database": result[0],
                "user": result[1],
                "version": result[2]
            }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
