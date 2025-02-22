from uuid import UUID

from azure.storage.blob import ContainerClient
from datastore.blob.azure_storage_api import (
    GetBlobError,
    build_blob_name,
    build_container_name,
    get_blob,
)
from datastore.db.queries.picture import get_picture_set_pictures
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.exceptions import FileNotFoundError


async def read_folder(
    cp: ConnectionPool, user_id: UUID | str, picture_set_id: UUID | str
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)
    if not isinstance(picture_set_id, UUID):
        picture_set_id = UUID(picture_set_id)

    with cp.connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
        pictures = get_picture_set_pictures(cursor, picture_set_id)
        file_ids: list[UUID] = [p["id"] for p in pictures]
        return file_ids


async def read_file(
    connection_string: str,
    user_id: UUID | str,
    folder_id: UUID | str,
    file_id: UUID | str,
):
    if not isinstance(user_id, UUID):
        user_id = UUID(user_id)
    if not isinstance(folder_id, UUID):
        folder_id = UUID(folder_id)
    if not isinstance(file_id, UUID):
        file_id = UUID(file_id)

    container_client = ContainerClient.from_connection_string(
        connection_string, container_name=build_container_name(str(user_id))
    )
    blob_name = build_blob_name(str(folder_id), str(file_id))

    try:
        blob: bytes = await get_blob(container_client, blob_name)
        return blob
    except GetBlobError as e:
        if "The specified blob does not exist." in str(e):
            raise FileNotFoundError(
                f"File {file_id} not found in folder {folder_id}"
            ) from e
        raise
