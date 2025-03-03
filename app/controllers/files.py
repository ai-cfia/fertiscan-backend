import io
import json
from uuid import UUID

import filetype
from datastore.db.metadata.picture_set import build_picture_set_metadata
from PIL import Image
from psycopg.rows import dict_row
from psycopg.sql import SQL
from psycopg_pool import ConnectionPool

from app.exceptions import (
    FileCreationError,
    FileNotFoundError,
    FolderCreationError,
    FolderDeletionError,
    FolderNotFoundError,
    FolderReadError,
    StorageFileNotFound,
    UserNotFoundError,
    log_error,
)
from app.models.files import Folder, UploadedFile
from app.models.users import User
from app.services.file_storage import FertiscanStorage


async def read_inspection_folders(
    cp: ConnectionPool, fs: FertiscanStorage, user_id: UUID | str
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        query = SQL("""
            SELECT 
                ps.*,
                COALESCE(json_agg(p.id), '[]') AS file_ids
            FROM picture_set ps
            JOIN picture p ON ps.id = p.picture_set_id
            WHERE ps.owner_id = %s
            GROUP BY ps.id;
        """)
        cursor.execute(query, (user_id,))
        folders = cursor.fetchall()
        folders = [Folder.model_validate(f) for f in folders]
        for f in folders:
            db_filenames = [str(id) for id in f.file_ids]
            filenames = fs.read_inspection_folder(user_id, str(f.id))
            if set(db_filenames) != set(filenames):
                raise FolderReadError(
                    f"Folder {f.id} has inconsistent file list between database and storage"
                )
        return folders


async def read_inspection_folder(
    cp: ConnectionPool,
    fs: FertiscanStorage,
    user_id: UUID | str,
    picture_set_id: UUID | str,
) -> Folder:
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)
    if not isinstance(picture_set_id, UUID):
        picture_set_id = UUID(picture_set_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        query = SQL(
            """
            SELECT 
                ps.*, 
                COALESCE(json_agg(p.id), '[]') AS file_ids
            FROM picture_set ps
            JOIN picture p ON ps.id = p.picture_set_id
            WHERE ps.owner_id = %s AND ps.id = %s
            GROUP BY ps.id;
            """
        )
        cursor.execute(query, (user_id, picture_set_id))
        if (folder := cursor.fetchone()) is None:
            raise FolderNotFoundError(f"Folder {picture_set_id} not found")
        folder = Folder.model_validate(folder)
        filenames = fs.read_inspection_folder(user_id, str(folder.id))
        if set(folder.file_ids) != set(filenames):
            raise FolderReadError(
                f"Folder {folder.id} has inconsistent file list between database and storage"
            )
        return folder


async def create_inspection_folder(
    cp: ConnectionPool,
    fs: FertiscanStorage,
    user_id: UUID | str,
    labels: list[bytes],
    name: str | None = None,
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        query = SQL("SELECT * FROM users WHERE id = %s;")
        cursor.execute(query, (user_id,))
        if (user := cursor.fetchone()) is None:
            raise UserNotFoundError(f"User {user_id} not found")
        user = User.model_validate(user)
        picture_set_metadata = build_picture_set_metadata(user.id, len(labels))
        # create picture set or get default set
        query = SQL(
            """
            INSERT INTO picture_set (
                picture_set,
                owner_id,
                name
            ) VALUES (%s, %s, %s)
            RETURNING *;
            """
        )
        cursor.execute(query, (picture_set_metadata, user.id, name))
        if (folder := cursor.fetchone()) is None:
            query = SQL(
                """
                SELECT ps.*
                FROM picture_set ps
                JOIN users u ON ps.id = u.default_set_id
                WHERE u.id = %s;
                """
            )
            cursor.execute(query, (user.id,))
            if (folder := cursor.fetchone()) is None:
                raise FolderCreationError("Error creating folder")

        folder = Folder.model_validate(folder)

        # save each file
        for i, f in enumerate(labels):
            # in db
            kind = filetype.guess(f)
            mime_type = kind.mime if kind else "application/octet-stream"
            img = Image.open(io.BytesIO(f))
            metadata = json.dumps(
                {
                    "mime_type": mime_type,
                    "size": len(f),
                    "sort_order": i,
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                }
            )
            query = SQL(
                """
                INSERT INTO picture (
                    picture,
                    picture_set_id,
                    nb_obj
                ) VALUES (%s, %s, %s)
                RETURNING *;
                """
            )
            cursor.execute(query, (metadata, folder.id, len(labels)))
            if (file := cursor.fetchone()) is None:
                raise FileCreationError("File creation failed for unknown reason")
            file = UploadedFile.model_validate(file)
            # in storage
            fs.save_label(str(user.id), str(folder.id), str(file.id), f)
            folder.file_ids.append(file.id)
        return folder


async def delete_inspection_folder(
    cp: ConnectionPool,
    fs: FertiscanStorage,
    user_id: UUID | str,
    folder_id: UUID | str,
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)
    if not isinstance(folder_id, UUID):
        folder_id = UUID(folder_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        query = SQL("SELECT * FROM users WHERE id = %s;")
        cursor.execute(query, (user_id,))
        if (user := cursor.fetchone()) is None:
            raise UserNotFoundError(f"User {user_id} not found")
        user = User.model_validate(user)
        if user.default_folder_id == folder_id:
            raise FolderDeletionError("Cannot delete default picture set")
        query = SQL(
            "DELETE FROM picture_set WHERE id = %s AND owner_id = %s RETURNING *;"
        )
        cursor.execute(query, (folder_id, user.id))
        if (deleted_folder := cursor.fetchone()) is None:
            raise FolderNotFoundError(f"Folder {folder_id} not found")
        deleted_folder = Folder.model_validate(deleted_folder)
        try:
            fs.delete_inspection_folder(
                str(user.id),
                str(folder_id),
            )
        except Exception as e:
            log_error(e)
            raise FolderDeletionError(
                f"Error deleting folder {folder_id} from storage"
            ) from e
        return deleted_folder


async def read_label(
    fs: FertiscanStorage,
    user_id: UUID | str,
    folder_id: UUID | str,
    label_id: UUID | str,
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)
    if not isinstance(folder_id, UUID):
        folder_id = UUID(folder_id)
    if not isinstance(label_id, UUID):
        label_id = UUID(label_id)

    try:
        return fs.read_label(
            user_id,
            str(folder_id),
            str(label_id),
        )
    except StorageFileNotFound as e:
        raise FileNotFoundError(f"{e}") from e
