# app/api/cleanup.py

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_session
from background_tasks import cleanup_tokens_background_task
from app.config.settings import CLEANUP_ROUTE
from fastapi.middleware.cors import CORSMiddleware
router = APIRouter()

@router.get(CLEANUP_ROUTE)
async def cleanup_tokens_route(background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    cleanup_tokens_background_task(background_tasks, db)