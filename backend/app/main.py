from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.db import get_db, Base, engine

app = FastAPI(title=settings.PROJECT_NAME)

Base.metadata.create_all(bind=engine)

@app.get('/')
def test_app():
    return "Hello Hossein"

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get('/health_database')
def check_database_connection(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        # "debug_mode": settings.DEBUG
    }