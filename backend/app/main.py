from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.db import get_db, Base, engine
from app.routers import document

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(document.router)

Base.metadata.create_all(bind=engine)

# test fastapi itself
@app.get('/')
def test_app():
    return "Hello Hossein"

# test conntction UI and FastAPI
@app.get('/health_ui')
def check_database_connection(db: Session = Depends(get_db)):
    return {"message": "Backend connectin is successful"}


# test db connection
@app.get('/health_db')
def check_database_connection(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        # "debug_mode": settings.DEBUG
    }