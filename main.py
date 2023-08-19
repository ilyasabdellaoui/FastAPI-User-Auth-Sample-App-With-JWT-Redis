# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import ALLOWED_ORIGINS
from app.api.auth import user_routes, auth_routes  # Import your API routers here
from app.api import cleanup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API routers here
app.include_router(user_routes.router, prefix="/user", tags=["user"])
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(cleanup.router, prefix="/api", tags=["api"])