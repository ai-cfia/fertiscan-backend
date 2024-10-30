from http import HTTPStatus

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pipeline import GPT, OCR

from app.connection_manager import ConnectionManager
from app.models.users import User

auth = HTTPBasic()


def get_connection_manager(request: Request) -> ConnectionManager:
    """
    Returns the app's ConnectionManager instance.
    """
    return request.app.connection_manager


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
