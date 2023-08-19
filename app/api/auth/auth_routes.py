import jwt
from requests import Session
from fastapi import APIRouter, Depends, HTTPException, Header, Request

from app.db.schemas import UserCreate, RequestDetails, UserUpdate
from app.db.database import get_session

from app.config.settings import ALGORITHM, JWT_SECRET_KEY
from app.utils.jwt_utils import JWTBearer
from app.utils.rate_limit import rate_limiter

from .auth_services import login, logout_user, register_user

router = APIRouter()


@router.post("/register")
async def register(
    user: UserCreate,
    api_key: str = Header(None),
    session: Session = Depends(get_session),
    request: Request = None,
    dependency: None = Depends(rate_limiter),
):
    return register_user(user, session, request, dependency)

@router.post('/login')
def user_login(request: RequestDetails, api_key: str = Header(None), db: Session = Depends(get_session)):
    return login(request, db)


@router.post('/logout')
def logout_route(api_key: str = Header(None), token: str = Depends(JWTBearer()), db: Session = Depends(get_session)):
    payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
    user_id = payload['sub']

    logout_user(db, user_id, token)

    return {"message": "Logout Successfully"}
