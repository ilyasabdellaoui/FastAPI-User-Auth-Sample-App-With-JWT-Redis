from datetime import timedelta
from fastapi import HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.db.models import User, TokenTable
from app.db.schemas import UserCreate, RequestDetails, RequestDetails, UserCreate

from app.utils.token_utils import get_hashed_password, verify_password, create_access_token, create_refresh_token
from app.utils.rate_limit import redis_client, update_request_info
from app.utils.validators import validate_email, validate_password

from app.config.settings import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES

###################################################################################################
#                                       REGISTER USER                                             #
###################################################################################################
def register_user(user: UserCreate, session: Session, request: Request, dependency: None):
    redis_key = "rate_limit:" + request.client.host
    existing_user = session.query(User).filter_by(email=user.email).first()
    if existing_user:
        update_request_info(redis_client, redis_key, "failed")
        raise HTTPException(status_code=400, detail="Email already registered")

    is_valid_email = validate_email(user.email)
    if not is_valid_email:
        update_request_info(redis_client, redis_key, "failed")
    
    # Validate the password
    is_valid_password = validate_password(user.password)
    if not is_valid_password:
        update_request_info(redis_client, redis_key, "failed")

    encrypted_password = get_hashed_password(user.password)

    # Set default values for username and currency if not provided
    if user.username is None or user.username == "":
        user.username = user.email.split("@")[0]
    if user.currency is None or user.currency == "":
        user.currency = "EUR"

    new_user = User(username=user.username, email=user.email, password=encrypted_password, currency=user.currency)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Return a redirection response to the login page with email and password in the request body
    response = Response(status_code=308)  # Use 308 to indicate a permanent redirect
    response.headers["Location"] = "/login"  # Replace with your actual login page URL
    response.content = f"email={user.email}&password={user.password}"
    update_request_info(redis_client, redis_key, "success")
    return {"message": "User created successfully"}

###################################################################################################
#                                       LOGIN USER                                                #
###################################################################################################
def login(request: RequestDetails, db: Session):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email")
    hashed_pass = user.password
    if not verify_password(request.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access = create_access_token(user.user_id, expires_delta=access_token_expires)
    refresh = create_refresh_token(user.user_id, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    user_id = user.user_id
    username = user.username
    email = user.email
    currency = user.currency

    token_db = TokenTable(user_id=user.user_id,  access_token=access,  refresh_token=refresh, status=True)
    db.add(token_db)
    db.commit()
    db.refresh(token_db)
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "currency": currency,
        "access_token": access,
        "refresh_token": refresh,
    }

###################################################################################################
#                                       LOGOUT USER                                               #
###################################################################################################
def logout_user(db: Session, user_id: int, token: str):
    existing_token = db.query(TokenTable).filter(TokenTable.user_id == user_id, TokenTable.access_token == token).first()
    if existing_token:
        existing_token.status = False
        db.add(existing_token)
        db.commit()
        db.refresh(existing_token)
    else:
        raise HTTPException(status_code=400, detail="Invalid access token")
    return {"message": "Logout Successfully"}
