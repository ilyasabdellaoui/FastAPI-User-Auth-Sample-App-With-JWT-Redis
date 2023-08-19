import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
#Postgres connection url
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the PostgreSQL engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Create session
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()