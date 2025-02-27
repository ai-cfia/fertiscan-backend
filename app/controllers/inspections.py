import asyncio
from uuid import UUID

from azure.storage.blob import ContainerClient
from datastore.blob.azure_storage_api import build_container_name
from fertiscan import delete_inspection as db_delete_inspection
from fertiscan import get_full_inspection_json, get_user_analysis_by_verified
from fertiscan import update_inspection as db_update_inspection
from fertiscan.db.metadata.inspection import build_inspection_import
from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)
from fertiscan.db.queries.inspection import new_inspection_with_label_info
from psycopg_pool import ConnectionPool

from app.exceptions import InspectionNotFoundError, MissingUserAttributeError, log_error
from app.models.inspections import (
    DeletedInspection,
    Inspection,
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
                main_organization_id=entry[7],
                main_organization_name=entry[8],
                verified=entry[9],
            )
            for sublist in inspections
            for entry in sublist
        ]

        return inspections


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
    cp: ConnectionPool, user: User, label_data: LabelData | dict
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for creating inspections.")
    if not isinstance(label_data, LabelData):
        label_data = LabelData.model_validate(label_data)

    with cp.connection() as conn, conn.cursor() as cursor:
        formatted_analysis = build_inspection_import(
            label_data.model_dump(mode="json"), user.id, label_data.picture_set_id
        )
        inspection = new_inspection_with_label_info(cursor, user.id, formatted_analysis)
        inspection = Inspection.model_validate(inspection)
        return inspection


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
        connection_string, container_name=build_container_name(str(user.id))
    )

    with cp.connection() as conn, conn.cursor() as cursor:
        deleted = await db_delete_inspection(cursor, id, user.id, container_client)
        return DeletedInspection.model_validate(deleted.model_dump())
