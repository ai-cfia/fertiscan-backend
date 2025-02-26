from uuid import UUID

from fertiscan import (
    new_inspection,
    get_inspection as get_inspection_controller,
    get_user_analysis_by_verified,
)

from fertiscan.db.queries.inspection import (
    get_inspection_dict,
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
        verified_inspections = get_user_analysis_by_verified(cursor, user.id, True)
        unverified_inspections = get_user_analysis_by_verified(cursor, user.id, False)
        inspections = [verified_inspections, unverified_inspections]

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
            inspection = get_inspection_dict(cursor, id)
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e
        return InspectionResponse.model_construct(inspection)


async def create_inspection(
    cp: ConnectionPool,
    user: User,
    label_data: LabelData,
    label_images: list[bytes],
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required for creating inspections.")
    if not label_data:
        raise ValueError("Label data is required for creating inspection.")

    with cp.connection() as conn, conn.cursor() as cursor:
        inspection_data = label_data.model_dump(mode="json")
        inspection = new_inspection(cursor, user.id, inspection_data)
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
        controller = get_inspection_controller(user.id, id)
        inspection_data = inspection.model_dump(mode="json")
        try:
            result = controller.update_inspection(cursor, user.id, inspection_data)
        except DBInspectionNotFoundError as e:
            log_error(e)
            raise InspectionNotFoundError(f"{e}") from e
        return InspectionResponse.model_validate(result.model_dump())


async def delete_inspection(
    cp: ConnectionPool,
    user: User,
    id: UUID | str,
):
    if not user.id:
        raise MissingUserAttributeError("User ID is required to delete an inspection.")
    if not id:
        raise ValueError("Inspection ID is required for deletion.")
    if not isinstance(id, UUID):
        id = UUID(id)

    with cp.connection() as conn, conn.cursor() as cursor:
        controller = get_inspection_controller(cursor, id)
        deleted = controller.delete_inspection(cursor, user.id)
        return DeletedInspection.model_validate(deleted.model_dump())
