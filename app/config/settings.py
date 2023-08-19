import os
from dotenv import load_dotenv
load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")

# SendGrid settings
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

SERVER_URL = "http://localhost:8000"
FRONT_END_URL = "http://127.0.0.1:5500"
CLEANUP_ROUTE = "/cleanup-tokens"

# CORS settings
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",  
]

# Other settings
CLEANUP_INTERVAL_HOURS = 24