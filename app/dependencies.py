from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool

from app.config import Settings
from app.controllers.users import sign_in
from app.exceptions import UserNotFoundError
from app.models.label_data import LabelData
from app.models.users import User

auth = HTTPBasic()


def get_settings(request: Request) -> Settings:
    return request.app.settings


def get_connection_pool(request: Request) -> ConnectionPool:
    return request.app.pool


def get_ocr(request: Request) -> OCR:
    return request.app.ocr


def get_gpt(request: Request) -> GPT:
    return request.app.gpt


def authenticate_user(credentials: HTTPBasicCredentials = Depends(auth)):
    if not credentials.username:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!"
        )

    return User(username=credentials.username)


async def fetch_user(
    auth_user: User = Depends(authenticate_user),
    cp: ConnectionPool = Depends(get_connection_pool),
) -> User:
    try:
        return await sign_in(cp, auth_user)
    except UserNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid username or password"
        )


def validate_files(files: list[UploadFile] = File(..., min_length=1)):
    for f in files:
        if f.size == 0:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"File {f.filename} is empty",
            )
    return files


def get_label_data(label_data: Annotated[LabelData | str, Form(...)]):
    if isinstance(label_data, str):
        return LabelData.model_validate_json(label_data)
    return label_data
