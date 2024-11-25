from typing import Annotated
from functools import lru_cache
from http import HTTPStatus

from fastapi import Depends, File, HTTPException, Request, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool

from app.config import Settings

from app.controllers.users import sign_in
from app.exceptions import UserNotFoundError
from app.models.users import User
from app.models.jwt import Token

auth = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@lru_cache
def get_settings():
    return Settings()


def get_connection_pool(request: Request) -> ConnectionPool:
    """
    Returns the app's connection pool.
    """
    return request.app.pool


def get_ocr(request: Request) -> OCR:
    """
    Returns the app's OCR instance.
    """
    return request.app.ocr


def get_gpt(request: Request) -> GPT:
    """
    Returns the app's GPT instance.
    """
    return request.app.gpt


def authenticate_user(credentials: HTTPBasicCredentials = Depends(auth)):
    """
    Authenticates a user.
    """
    if not credentials.username:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!"
        )

    return User(username=credentials.username)

def authenticate_user_oauth2(form_data: OAuth2PasswordRequestForm = Depends(oauth2_scheme)):
    """
    Authenticates a user.
    """
    if not form_data.username:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!"
        )

    return User(username=form_data.username)

async def fetch_user(
    auth_user: User = Depends(authenticate_user),
    cp: ConnectionPool = Depends(get_connection_pool),
) -> User:
    """
    Fetches the authenticated user's info from db.
    """
    try:
        return await sign_in(cp, auth_user)
    except UserNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid username or password"
        )

async def fetch_user_oauth2(
    auth_user: User = Depends(authenticate_user_oauth2),
    cp: ConnectionPool = Depends(get_connection_pool),
) -> User:
    """
    Fetches the authenticated user's info from db.
    """
    try:
        user = await sign_in(cp, auth_user)
        return Token(access_token=user.username, token_type="bearer", user=user)
    except UserNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid username or password"
        )

def validate_files(files: list[UploadFile] = File(..., min_length=1)):
    """
    Validates uploaded files.
    """
    for f in files:
        if f.size == 0:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"File {f.filename} is empty",
            )
    return files
