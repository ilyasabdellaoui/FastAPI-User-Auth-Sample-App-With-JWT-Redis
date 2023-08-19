from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import User
from app.db.schemas import (ForgotPasswordRequest, ResetPasswordRequest,
                            UserCreate, UserUpdate)
from app.utils.token_utils import get_authenticated_user_id

from .user_services import (delete_user, reset_user_password,
                            send_password_reset_email, update_user_profile)

from app.config.settings import FRONT_END_URL

router = APIRouter()

#########################################################################################################
#                                              UPDATE User                                              #
#########################################################################################################


@router.put('/update/{user_id}', response_model=UserUpdate)
def update_user_route(
    user_id: int,
    updated_user: UserUpdate,
    authenticated_user_id: int = Depends(get_authenticated_user_id),
    db: Session = Depends(get_session)
):
    return update_user_profile(db, user_id, updated_user, authenticated_user_id)

#########################################################################################################
#                                              DELETE User                                              #
#########################################################################################################


@router.delete('/delete/{user_id}')
def delete_user_route(
    user_id: int,
    deleted_user: UserCreate,
    authenticated_user_id: int = Depends(get_authenticated_user_id),
    db: Session = Depends(get_session)
):
    return delete_user(db, user_id, authenticated_user_id, deleted_user)

##########################################################################################################
#                                          SEND RESET PASSWORD LINK                                      #
##########################################################################################################


@router.post("/forgot-password")
async def forgot_password_route(request: ForgotPasswordRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return send_password_reset_email(db, user, FRONT_END_URL)

##########################################################################################################
#                                          RESET PASSWORD                                                #
##########################################################################################################


@router.post("/reset-password")
def reset_password_route(request: ResetPasswordRequest, db: Session = Depends(get_session)):
    return reset_user_password(db, request.reset_token, request.new_password)
