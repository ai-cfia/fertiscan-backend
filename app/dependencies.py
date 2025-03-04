from http import HTTPStatus

from fastapi import Depends, File, HTTPException, Request, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from psycopg_pool import ConnectionPool

from app.config import Settings
from app.controllers.users import sign_in
from app.exceptions import UserNotFoundError
from app.models.users import User

auth = HTTPBasic()


def get_settings(request: Request) -> Settings:
    return request.app.settings

def get_pipeline_settings(request: Request) -> Settings:
    return request.app.pipeline_settings


def get_connection_pool(request: Request) -> ConnectionPool:
    return request.app.pool

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
