from datetime import timedelta
from fastapi import BackgroundTasks, Depends
from sqlalchemy import func
import logging
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.models import TokenTable
from app.config.settings import ACCESS_TOKEN_EXPIRE_MINUTES, CLEANUP_INTERVAL_HOURS, SERVER_URL, CLEANUP_ROUTE
from app.db.database import get_session

scheduler = BackgroundScheduler()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dependency Injection
def start_cleanup_scheduler(scheduler: BackgroundScheduler):
    scheduler.add_job(send_cleanup_tokens_request, trigger=IntervalTrigger(hours=CLEANUP_INTERVAL_HOURS))
    scheduler.start()

def send_cleanup_tokens_request():
    try:
        cleanup_url = SERVER_URL + '/api'+ CLEANUP_ROUTE
        response = requests.get(cleanup_url)
        response.raise_for_status()  # Raise exception for non-2xx status codes
        logger.info("Cleanup request successful: %s", response.json())
    except requests.exceptions.RequestException as e:
        logger.error("Cleanup request failed: %s", str(e))

# Start the scheduler with dependency injection
start_cleanup_scheduler(scheduler)

# Define the actual token cleanup logic
def perform_token_cleanup(db):
    # Get the current timestamp from the database
    db_timestamp = db.query(func.current_timestamp()).scalar()
    # Mark expiring tokens as expired (soft delete)
    expiration_threshold = db_timestamp - timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Batch update to mark tokens as expired
    update_query = db.query(TokenTable).filter(
        TokenTable.status == True,
        TokenTable.created_date < expiration_threshold
    ).update(
        {TokenTable.status: False},
        synchronize_session=False
    )
    db.commit()
    # Batch delete expired tokens (permanently remove from database)
    delete_query = db.query(TokenTable).filter(TokenTable.status == False).delete(
        synchronize_session=False
    )
    db.commit()
    return {"message": "Tokens cleaned up successfully"}

# Define the cleanup background task
def cleanup_tokens_background_task(background_tasks: BackgroundTasks, db=Depends(get_session)):
    background_tasks.add_task(perform_token_cleanup, db)