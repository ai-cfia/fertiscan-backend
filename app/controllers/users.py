from datastore import UserAlreadyExistsError as DBUserAlreadyExistsError
from datastore import get_user, new_user
from datastore.db.queries.user import UserNotFoundError as DBUserNotFoundError
from fastapi.logger import logger
from psycopg_pool import ConnectionPool

from app.exceptions import (
    MissingUserAttributeError,
    UserConflictError,
    UserNotFoundError,
    log_error,
)
from app.models.users import User


async def sign_up(cp: ConnectionPool, user: User, connection_string: str) -> User:
    """
    Registers a new user in the system.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): The User instance containing the user's details.
        connection_string (str): The database connection string for setup.

    Raises:
        MissingUserAttributeError: Raised if the username is not provided.
        UserConflictError: Raised if a user with the same username already exists.

    Returns:
        User: The newly created User object with the assigned database ID.
    """
    if not user.username:
        raise MissingUserAttributeError("Username is required for sign-up.")

    try:
        with cp.connection() as conn, conn.cursor() as cursor:
            logger.debug(f"Creating user: {user.username}")
            user_db = await new_user(cursor, user.username, connection_string)
    except DBUserAlreadyExistsError as e:
        log_error(e)
        raise UserConflictError(f"User '{user.username}' already exists.") from e

    return user.model_copy(update={"id": user_db.id})


async def sign_in(cp: ConnectionPool, user: User) -> User:
    """
    Authenticates an existing user in the system.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): The User instance containing the user's details.

    Raises:
        MissingUserAttributeError: Raised if the username is not provided.
        UserNotFoundError: Raised if the user is not found in the database.

    Returns:
        User: The authenticated User object with the retrieved database ID.
    """
    if not user.username:
        raise MissingUserAttributeError("Username is required for sign-in.")

    try:
        with cp.connection() as conn, conn.cursor() as cursor:
            logger.debug(f"Fetching user ID for username: {user.username}")
            user_db = await get_user(cursor, user.username)
    except DBUserNotFoundError as e:
        log_error(e)
        raise UserNotFoundError(f"User '{user.username}' not found.") from e

    return user.model_copy(update={"id": user_db.id})
