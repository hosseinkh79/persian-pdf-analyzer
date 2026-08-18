from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# 1. Create global database engine instance
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True 
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 3. Base class for ORM models
Base = declarative_base()

# 4. Dependency function for FastAPI endpoint lifecycle management
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()