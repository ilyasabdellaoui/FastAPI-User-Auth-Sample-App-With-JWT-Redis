import re
from fastapi import HTTPException

#Email constraints /\S+@\S+\.\S+/;
def validate_email(email: str):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    return True

# Password Validation
def validate_password(new_password):
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not any(char.isupper() for char in new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not any(char.islower() for char in new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")
    if not any(char in "!@#$%^&*()-_+=:." for char in new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")
    return True