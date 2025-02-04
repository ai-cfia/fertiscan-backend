import asyncio
from uuid import UUID

from azure.storage.blob import ContainerClient
from fertiscan import delete_inspection as db_delete_inspection
from fertiscan import (
    get_full_inspection_json,
    get_user_analysis_by_verified,
    register_analysis,
)
from fertiscan.db.queries.inspection import get_inspection_dict
from datastore.db.queries.picture import (
    get_picture_set_pictures
)
from fertiscan import update_inspection as db_update_inspection
from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)
from psycopg_pool import ConnectionPool

from app.exceptions import InspectionNotFoundError, MissingUserAttributeError, log_error
from app.models.inspections import (
    DeletedInspection,
    InspectionData,
    InspectionResponse,
    InspectionUpdate,
)
from app.models.label_data import LabelData
from app.models.users import User


async def read_all_inspections(cp: ConnectionPool, user: User):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for fetching inspections.")

    with cp.connection() as conn, conn.cursor() as cursor:
        inspections = await asyncio.gather(
            get_user_analysis_by_verified(cursor, user.id, True),
            get_user_analysis_by_verified(cursor, user.id, False),
        )

        inspections = [
            InspectionData(
                id=entry[0],
                upload_date=entry[1],
                updated_at=entry[2],
                sample_id=entry[3],
                picture_set_id=entry[4],
                label_info_id=entry[5],
                product_name=entry[6],
                manufacturer_info_id=entry[7],
                company_info_id=entry[8],
                company_name=entry[9],
            )
            for sublist in inspections
            for entry in sublist
        ]

        return inspections

async def get_pictures(cp: ConnectionPool, id: UUID | str):
    """
    Retrieves the pictures associated with a user by inspection ID.
    """
    if not id:
        raise ValueError("Inspection ID is required for fetching inspection details.")
    if not isinstance(id, UUID):
        id = UUID(id)

    with cp.connection() as conn, conn.cursor() as cursor:
        try:
            inspection = get_inspection_dict(cursor, id)
            if inspection is None:
                raise InspectionNotFoundError(f"Inspection not found for ID {id}")
            
            picture_set_id = inspection.get("picture_set_id")
            if picture_set_id is None:
                log_error(f"Picture set not found for inspection {id}")
                raise DBInspectionNotFoundError(f"Picture set not found for inspection {id}")
            
            return get_picture_set_pictures(cursor, picture_set_id) # TODO: This function will be deprecated
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e

async def read_inspection(cp: ConnectionPool, user: User, id: UUID | str):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for fetching inspections.")
    if not id:
        raise ValueError("Inspection ID is required for fetching inspection details.")
    if not isinstance(id, UUID):
        id = UUID(id)

    with cp.connection() as conn, conn.cursor() as cursor:
        try:
            inspection = await get_full_inspection_json(cursor, id, user.id)
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e
        return InspectionResponse.model_validate_json(inspection)


async def create_inspection(
    cp: ConnectionPool,
    user: User,
    label_data: LabelData,
    label_images: list[bytes],
    connection_string: str,
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for creating inspections.")
    if not label_data:
        raise ValueError("Label data is required for creating inspection.")
    if not connection_string:
        raise ValueError("Connection string is required for creating inspection.")

    with cp.connection() as conn, conn.cursor() as cursor:
        container_client = ContainerClient.from_connection_string(
            connection_string, container_name=f"user-{user.id}"
        )
        label_data = label_data.model_dump(mode="json")
        inspection = await register_analysis(
            cursor, container_client, user.id, label_images, label_data
        )
        return InspectionResponse.model_validate(inspection)


async def update_inspection(
    cp: ConnectionPool,
    user: User,
    id: str | UUID,
    inspection: InspectionUpdate,
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for updating inspections.")
    if not id:
        raise ValueError("Inspection ID is required for updating inspection details.")
    if not inspection:
        raise ValueError("Inspection details are required for updating inspection.")

    if not isinstance(id, UUID):
        id = UUID(id)

    with cp.connection() as conn, conn.cursor() as cursor:
        inspection_data = inspection.model_dump(mode="json")
        try:
            result = await db_update_inspection(cursor, id, user.id, inspection_data)
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e
        return InspectionResponse.model_validate(result.model_dump())


async def delete_inspection(
    cp: ConnectionPool,
    user: User,
    id: UUID | str,
    connection_string: str,
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required to delete an inspection.")
    if not id:
        raise ValueError("Inspection ID is required for deletion.")
    if not connection_string:
        raise ValueError("Connection string is required for blob storage access.")
    if not isinstance(id, UUID):
        id = UUID(id)

    container_client = ContainerClient.from_connection_string(
        connection_string, container_name=f"user-{user.id}"
    )

    with cp.connection() as conn, conn.cursor() as cursor:
        deleted = await db_delete_inspection(cursor, id, user.id, container_client)
        return DeletedInspection.model_validate(deleted.model_dump())
