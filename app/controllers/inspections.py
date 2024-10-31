import asyncio

from fertiscan import get_user_analysis_by_verified

from app.connection_manager import ConnectionManager
from app.exceptions import MissingUserAttributeError
from app.models.inspection import InspectionData
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
