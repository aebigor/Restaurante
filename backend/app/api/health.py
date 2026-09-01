from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(
    prefix="/system",
    tags=["Sistema"]
)


@router.get("/")
def info():

    return {
        "status": "online",
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }


@router.get("/health")
def health():

    return {
        "status": "ok"
    }


@router.get("/database")
def database(db: Session = Depends(get_db)):

    db.execute(text("SELECT 1"))

    return {
        "database": "connected"
    }