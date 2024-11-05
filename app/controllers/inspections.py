import asyncio
from uuid import UUID

from azure.storage.blob import ContainerClient
from fertiscan import delete_inspection as db_delete_inspection
from fertiscan import (
    get_full_inspection_json,
    get_user_analysis_by_verified,
    register_analysis,
)
from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)
from psycopg_pool import ConnectionPool

from app.exceptions import InspectionNotFoundError, MissingUserAttributeError, log_error
from app.models.inspections import Inspection, InspectionData
from app.models.label_data import LabelData
from app.models.users import User


async def read_all_inspections(cp: ConnectionPool, user: User):
    """
    Retrieves all inspections associated with a user, both verified and unverified.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): User instance containing user details, including the user ID.

    Returns:
        list[InspectionData]: A list of `InspectionData` objects representing
        all inspections related to the user, including details like `upload_date`,
        `updated_at`, `product_name`, and more.

    Raises:
        MissingUserAttributeError: Raised if the user ID is missing.
    """
    if not user.id:
        raise MissingUserAttributeError("User ID is required for fetching inspections.")

    with cp.connection() as conn, conn.cursor() as cursor:
        inspections = await asyncio.gather(
            get_user_analysis_by_verified(cursor, user.id, True),
            get_user_analysis_by_verified(cursor, user.id, False),
        )

        # Flatten and transform results into InspectionData objects
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


async def read_inspection(cp: ConnectionPool, user: User, id: UUID | str):
    """
    Retrieves a specific inspection associated with a user by inspection ID.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): User instance containing user details, including the user ID.
        id (UUID | str): Unique identifier of the inspection, as a UUID or a string convertible to UUID.

    Returns:
        Inspection: An `Inspection` object with the inspection details.

    Raises:
        MissingUserAttributeError: Raised if the user ID is missing.
        ValueError: Raised if the inspection ID is not provided.
        InspectionNotFoundError: Raised if the inspection with the given ID is not found.
    """
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
        return Inspection.model_validate_json(inspection)


async def create_inspection(
    cp: ConnectionPool,
    user: User,
    label_data: LabelData,
    label_images: list[bytes],
    connection_string: str,
):
    """
    Creates a new inspection record associated with a user.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): User instance containing user details, including the user ID.
        label_data (LabelData): Data model containing label information required for the inspection.
        label_images (list[bytes]): List of images (in byte format) to be associated with the inspection.
        connection_string (str): Connection string for blob storage.

    Returns:
        Inspection: An `Inspection` object with the newly created inspection details.

    Raises:
        MissingUserAttributeError: Raised if the user ID is missing.
    """
    if not user.id:
        raise MissingUserAttributeError("User ID is required for creating inspections.")

    with cp.connection() as conn, conn.cursor() as cursor:
        container_client = ContainerClient.from_connection_string(
            connection_string, container_name=f"user-{user.id}"
        )
        inspection = await register_analysis(
            cursor, container_client, user.id, label_images, label_data.model_dump()
        )

        return Inspection.model_validate(inspection)


async def delete_inspection(
    cp: ConnectionPool,
    user: User,
    id: UUID,
    connection_string: str,
):
    """
    Deletes an inspection record and its associated picture set from the database.

    Args:
        cp (ConnectionPool): The connection pool for database management.
        user (User): The user requesting the deletion.
        inspection_id (UUID): The UUID of the inspection to delete.
        connection_string (str): Connection string for Azure Blob Storage.

    Returns:
        Inspection: The deleted inspection data.

    Raises:
        MissingUserAttributeError: If the user ID is missing.
        ValueError: If inspection_id or connection_string are invalid.
        InspectionNotFoundError: If the inspection does not exist or deletion fails.
    """
    if not user.id:
        raise MissingUserAttributeError("User ID is required to delete an inspection.")
    if not id:
        raise ValueError("Inspection ID is required for deletion.")
    if not connection_string:
        raise ValueError("Connection string is required for blob storage access.")

    container_client = ContainerClient.from_connection_string(
        connection_string, container_name=f"user-{user.id}"
    )

    with cp.connection() as conn, conn.cursor() as cursor:
        return await db_delete_inspection(cursor, id, user.id, container_client)
