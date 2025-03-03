from uuid import UUID

from fastapi.logger import logger
from psycopg.rows import dict_row
from psycopg.sql import SQL
from psycopg_pool import ConnectionPool

from app.exceptions import (
    MissingUserAttributeError,
    StorageFileNotFound,
    UserConflictError,
    UserDeletionError,
    UserNotFoundError,
    log_error,
)
from app.models.users import User
from app.services.file_storage import StorageManager


async def sign_up(cp: ConnectionPool, user: User) -> User:
    if not user.username:
        raise MissingUserAttributeError("Username is required for sign-up.")

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        logger.debug(f"Creating user: {user.username}")

        query = SQL(
            "INSERT INTO users (email, default_set_id) "
            "SELECT %s, NULL "
            "WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = %s) "
            "RETURNING *;"
        )
        cursor.execute(query, (user.username, user.username))

        if (new_user := cursor.fetchone()) is None:
            raise UserConflictError(f"User '{user.username}' already exists.")

        return User.model_validate(new_user)


async def sign_in(cp: ConnectionPool, user: User) -> User:
    if not user.username:
        raise MissingUserAttributeError("Username is required for sign-in.")

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        logger.debug(f"Fetching user ID for username: {user.username}")
        query = SQL("SELECT * FROM users WHERE email = %s;")
        cursor.execute(query, (user.username,))
        if (user_db := cursor.fetchone()) is None:
            raise UserNotFoundError(f"User '{user.username}' not found.")
        return User.model_validate(user_db)


async def delete_user(
    cp: ConnectionPool, storage: StorageManager, user_id: UUID | str
) -> dict:
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        logger.debug(f"Deleting user with ID: {user_id}")

        query = SQL("DELETE FROM users WHERE id = %s RETURNING *;")
        cursor.execute(query, (str(user_id),))
        if (deleted_user := cursor.fetchone()) is None:
            raise UserNotFoundError(f"User with ID '{user_id}' not found.")
        deleted_user = User.model_validate(deleted_user)

        try:
            storage.delete_namespace(user_id)
        except StorageFileNotFound as e:
            log_error(e)
            raise UserDeletionError(f"{e}") from e
