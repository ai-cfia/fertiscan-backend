from datastore import UserAlreadyExistsError as DBUserAlreadyExistsError
from datastore import get_user, new_user
from datastore.db.queries.user import UserNotFoundError as DBUserNotFoundError
from fastapi.logger import logger

from app.connection_manager import ConnectionManager
from app.constants import FERTISCAN_STORAGE_URL
from app.exceptions import (
    MissingUsernameError,
    UserConflictError,
    UserNotFoundError,
    log_error,
)
from app.models.users import User


async def sign_up(cm: ConnectionManager, user: User) -> User:
    """
    Registers a new user in the system.

    Args:
        cm (ConnectionManager): Database connection manager.
        user (User): User instance containing user details.

    Raises:
        MissingUsernameError: If the username is not provided.
        UserConflictError: If a user with the same username already exists.

    Returns:
        User: User object with assigned ID from the database.
    """
    if not user.username:
        raise MissingUsernameError("Username is required for sign-up.")

    try:
        with cm, cm.get_cursor() as cursor:
            logger.debug(f"Creating user: {user.username}")
            user_db = await new_user(cursor, user.username, FERTISCAN_STORAGE_URL)
    except DBUserAlreadyExistsError as e:
        log_error(e)
        raise UserConflictError(f"User '{user.username}' already exists.") from e

    return user.model_copy(update={"id": user_db.id})


async def sign_in(cm: ConnectionManager, user: User) -> User:
    """
    Authenticates an existing user in the system.

    Args:
        cm (ConnectionManager): Database connection manager.
        user (User): User instance containing user details.

    Raises:
        MissingUsernameError: If the username is not provided.
        UserNotFoundError: If the user is not found in the database.

    Returns:
        User: User object with the retrieved ID from the database.
    """
    if not user.username:
        raise MissingUsernameError("Username is required for sign-in.")

    try:
        with cm, cm.get_cursor() as cursor:
            logger.debug(f"Fetching user ID for username: {user.username}")
            user_db = await get_user(cursor, user.username)
    except DBUserNotFoundError as e:
        log_error(e)
        raise UserNotFoundError(f"User '{user.username}' not found.") from e

    return user.model_copy(update={"id": user_db.id})
