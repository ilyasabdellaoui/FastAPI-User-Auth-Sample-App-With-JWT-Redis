from pydantic import BaseModel
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    currency: str

class UserUpdate(BaseModel):
    new_email: str
    new_username: str
    old_password: str
    new_password: str
    new_currency: str        

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

# Request User Details Schema
class RequestDetails(BaseModel):
    email: str
    password: str

# Authentication Schemas
class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str

class TokenCreate(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    status: bool
    created_date: datetime