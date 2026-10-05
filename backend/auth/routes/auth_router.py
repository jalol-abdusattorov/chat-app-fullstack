from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from auth.models.token import Token
from auth.services.auth_service import authenticate_user, create_access_token


auth_router = APIRouter(
    prefix="/auth",
    tags=['Auth']
)

@auth_router.post("/login")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={'sub': user['email'], 'uid': str(user['_id'])},
        expires_delta=access_token_expires
    )

    return {"token": Token(access_token=access_token, token_type="bearer"), 'id': str(user['_id'])}