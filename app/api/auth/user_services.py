import jwt
from jwt import DecodeError
from jose import ExpiredSignatureError
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import TokenTable, User
from app.db.schemas import UserCreate, UserUpdate

from app.utils.token_utils import (ALGORITHM, JWT_SECRET_KEY,
                                   create_access_token, create_refresh_token,
                                   get_hashed_password, password_context)
from app.utils.validators import validate_email, validate_password

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config.settings import (EMAIL_FROM, REFRESH_TOKEN_EXPIRE_MINUTES,
                        SENDGRID_API_KEY)

#########################################################################################################
#                                              UPDATE User                                              #
#########################################################################################################
def update_user_profile(db: Session, user_id: int, updated_user: UserUpdate, authenticated_user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Ensure the authenticated user is updating their own profile
    if authenticated_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this user's profile")

    # Verify the provided old password against the existing password hash
    existing_password_hash = user.password
    if not password_context.verify(updated_user.old_password, existing_password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    # Ensure the new email is not already registered
    if updated_user.new_email is None or updated_user.new_email == "":
        updated_user.new_email = user.email
    elif updated_user.new_email != user.email:
        existing_user = db.query(User).filter(User.email == updated_user.new_email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    else:
        validate_email(updated_user.new_email)

    # Pass the default value of the old password if the new password is not provided
    if updated_user.new_password is None or updated_user.new_password == "":
        updated_user.new_password = updated_user.old_password

    if updated_user.new_username is None or updated_user.new_username == "":
        updated_user.new_username = user.username

    if updated_user.new_currency is None or updated_user.new_currency == "":
        updated_user.new_currency = user.currency

    # Password validation
    validate_password(updated_user.new_password)
    hashed_password = get_hashed_password(updated_user.new_password)
    setattr(user, 'password', hashed_password)

    user.username = updated_user.new_username
    user.email = updated_user.new_email
    user.currency = updated_user.new_currency

    db.commit()
    db.refresh(user)
    return updated_user

#########################################################################################################
#                                              DELETE User                                              #
#########################################################################################################
def delete_user(db: Session, user_id: int, authenticated_user_id: int, deleted_user: UserCreate):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if authenticated_user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this user's profile")

    existing_password_hash = user.password
    if not password_context.verify(deleted_user.password, existing_password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

##########################################################################################################
#                                          SEND RESET PASSWORD LINK                                      #
##########################################################################################################
def send_password_reset_email(db, user, FRONT_END_URL):
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(user.user_id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.user_id, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    token_db = TokenTable(user_id=user.user_id,  access_token=access_token, refresh_token=refresh_token, status=True)
    db.add(token_db)
    db.commit()

    try:
        # Generate and send the password reset email
        reset_link = f"{FRONT_END_URL}/reset-password.html?token={access_token}"
        subject = "Password Reset"
        message = f"Click the following link to reset your password: {reset_link}"
        email_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{subject}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        background-color: #ffffff;
                        border-radius: 10px;
                        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                        padding: 40px;
                        max-width: 600px;
                        margin: 40px auto;
                    }}
                    .header {{
                        font-size: 32px;
                        color: #333;
                    }}
                    .cta-button {{
                        display: inline-block;
                        padding: 8px;
                        background-color: #007bff;
                        color: #fff;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 18px;
                        decoration: none;
                        underline: none;
                    }}
                    .footer {{
                        margin-top: 20px;
                        color: #777;
                        font-size: 18px;
                    }}

                    @media only screen and (max-width: 600px) {{
                        .container {{
                            padding: 20px;
                            max-width: 100%;
                        }}
                        .header {{
                            font-size: 28px;
                        }}
                        .cta-button {{
                            padding: 6px;
                            font-size: 16px;
                        }}
                        .footer {{
                            font-size: 14px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2 class="header">Password Reset</h2>
                    <p style="font-size: 18px;">Hello <span><b><i>{user.username}</i></b></span>,</p>
                    <p style="font-size: 16px;">You have requested to reset your password. Click the button below to proceed:</p>
                    <a href="{reset_link}" class="cta-button">Reset Password</a>
                    <p style="font-size: 16px;">If the button above does not work, copy and paste the following link into your browser:</p>
                    <p>{reset_link}</p>
                    <p style="font-size: 16px;">This link will expire in 15 minutes for security reasons.</p>
                    <p style="font-size: 16px;">If you did not request a password reset, please ignore this email.</p>
                    <p class="footer">Best regards,<br>BudgetTrackio Team</p>
                </div>
            </body>
            </html>
        """

        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=user.email,
            subject=subject,
            html_content=email_template
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code == 202:
            return {"message": "Password reset email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

##########################################################################################################
#                                          RESET PASSWORD                                                #
##########################################################################################################
def reset_user_password(db, reset_token: str, new_password: str):
    try:
        token = db.query(TokenTable).filter(TokenTable.access_token == reset_token).first()
        if token is None:
            raise HTTPException(status_code=404, detail="Invalid access token")

        if not token.status:
            raise HTTPException(status_code=400, detail="Expired access token")

        if token.access_token != reset_token:
            raise HTTPException(status_code=400, detail="Invalid access token")

        payload = jwt.decode(reset_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]

        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        validate_password(new_password)
        hashed_password = get_hashed_password(new_password)

        user.password = hashed_password
        token.status = False
        db.commit()
        return {"message": "Password reset successful"}

    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Expired access token")
    except DecodeError:
        raise HTTPException(status_code=400, detail="Invalid access token")