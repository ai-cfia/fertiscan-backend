import asyncio
from uuid import UUID

from azure.storage.blob import ContainerClient
from fertiscan import delete_inspection as db_delete_inspection
from fertiscan import (
    get_full_inspection_json,
    get_user_analysis_by_verified,
    register_analysis,
)
from fertiscan.db.queries.inspection import get_inspection_dict as get_inspection
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
    Inspection,
    InspectionData,
    InspectionUpdate,
)
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
            inspection = get_inspection(cursor, id)
            return get_picture_set_pictures(cursor, inspection['picture_set_id']) # TODO: This function will be deprecated
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e

async def read_inspection(cp: ConnectionPool, user: User, id: UUID | str):
    """
    Retrieves a specific inspection associated with a user by inspection ID.

    Args:
        cp (ConnectionPool): The connection pool to manage database connections.
        user (User): User instance containing user details, including the user ID.
        id (UUID | str): The UUID of the inspection to read.

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
        MissingUserAttributeError: If the user ID is missing.
        ValueError: If label data or connection string is missing.
    """
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
        return Inspection.model_validate(inspection)


async def update_inspection(
    cp: ConnectionPool,
    user: User,
    id: str | UUID,
    inspection: InspectionUpdate,
) -> Inspection:
    """
    Updates an existing inspection record associated with a user.

    Args:
        cp (ConnectionPool): Connection pool for managing database connections.
        user (User): User instance with user details, including user ID.
        id (str | UUID): Inspection ID for the record to update.
        inspection (InspectionUpdate): Contains updated inspection details.

    Returns:
        Inspection: The updated inspection record.

    Raises:
        MissingUserAttributeError: If the user ID is missing.
        ValueError: If inspection ID or details are missing.
        InspectionNotFoundError: If the inspection record does not exist.
    """
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
        return Inspection.model_validate(result.model_dump())


async def delete_inspection(
    cp: ConnectionPool,
    user: User,
    id: UUID | str,
    connection_string: str,
):
    """
    Deletes an inspection record and its associated picture set from the database.

    Args:
        cp (ConnectionPool): The connection pool for database management.
        user (User): The user requesting the deletion.
        id (UUID | str): The UUID of the inspection to delete.
        connection_string (str): Connection string for Azure Blob Storage.

    Returns:
        DeletedInspection: The deleted inspection data.

    Raises:
        MissingUserAttributeError: If the user ID is missing.
        ValueError: If id or connection_string are invalid.
    """
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
