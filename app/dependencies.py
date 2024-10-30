from http import HTTPStatus

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.models.users import User

auth = HTTPBasic()


def get_connection_manager(request: Request):
    """
    Returns the app's ConnectionManager instance.
    """
    return request.app.connection_manager


def authenticate_user(credentials: HTTPBasicCredentials = Depends(auth)):
    """
    Authenticates a user.
    """
    if not credentials.username:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!"
        )

    return User(username=credentials.username)
