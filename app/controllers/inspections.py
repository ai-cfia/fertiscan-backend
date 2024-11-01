import asyncio
from uuid import UUID

from fertiscan import get_full_inspection_json, get_user_analysis_by_verified
from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)

from app.connection_manager import ConnectionManager
from app.exceptions import InspectionNotFoundError, MissingUserAttributeError, log_error
from app.models.inspections import Inspection, InspectionData
from app.models.users import User


async def read_all(cm: ConnectionManager, user: User):
    """
    Retrieves all inspections associated with a user, both verified and unverified.

    Args:
        cm (ConnectionManager): Database connection manager.
        user (User): User instance containing user details, including the user ID.

    Returns:
        list[InspectionData]: A list of `InspectionData` objects representing
        all inspections related to the user, with fields such as `upload_date`,
        `updated_at`, `product_name`, and more.
    """

    if not user.id:
        raise MissingUserAttributeError("User id is required for fetching inspections.")

    with cm, cm.get_cursor() as cursor:
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


async def read(cm: ConnectionManager, user: User, id: UUID | str):
    """
    Retrieves a specific inspection associated with a user by inspection ID.

    Args:
        cm (ConnectionManager): Database connection manager.
        user (User): User instance containing user details, including the user ID.
        id (UUID | str): Unique identifier of the inspection, either as a UUID object or a string that can be converted to UUID.

    Returns:
        Inspection: An `Inspection` object representing the inspection details.

    Raises:
        MissingUserAttributeError: If the user ID is missing.
        ValueError: If the inspection ID is not provided.
        InspectionNotFoundError: If the inspection with the given ID is not found in the database.
    """

    if not user.id:
        raise MissingUserAttributeError("User id is required for fetching inspections.")

    if not id:
        raise ValueError("Inspection ID is required for fetching inspection details.")

    if not isinstance(id, UUID):
        id = UUID(id)

    with cm, cm.get_cursor() as cursor:
        try:
            inspection = await get_full_inspection_json(cursor, id, user.id)
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e
        return Inspection.model_validate_json(inspection)
