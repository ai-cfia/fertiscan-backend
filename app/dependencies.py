from typing import Annotated
from functools import lru_cache
from http import HTTPStatus
from fastapi import Depends, File, HTTPException, Request, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool
from app.config import Settings
from app.controllers.users import sign_in
from app.exceptions import UserNotFoundError
from app.models.users import User
from app.models.jwt import Token

import jwt

auth = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

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


def get_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Fetches the user's credentials.
    """
    return User(username=form_data.username)

def get_username(token: str = Depends(oauth2_scheme)) -> User:
    """
    Fetches the current user.
    """
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return User(username=username)
    except Exception:
        raise credentials_exception

async def auth_user(
    user: User = Depends(get_user),
    cp: ConnectionPool = Depends(get_connection_pool),
) -> Token:
    """
    Fetches the authenticated user's info from db.
    """
    try:
        user = await sign_in(cp, user)
        return Token(
            user=user,
            token_type="bearer",
            access_token=jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM),
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid username or password"
        )

async def fetch_user(
    username: Annotated[User, Depends(get_username)],
    cp: ConnectionPool = Depends(get_connection_pool),
) -> User:
    """
    Fetches the current authenticated user.
    """
    try:
        return await sign_in(cp, username)
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
