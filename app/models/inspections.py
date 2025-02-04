from datetime import datetime
from uuid import UUID

from fertiscan.db.metadata.inspection import DBInspection, Inspection
from fertiscan.db.metadata.inspection import (
    OrganizationInformation as DBOrganizationInformation,
)
from pydantic import BaseModel


class OrganizationInformation(DBOrganizationInformation):
    id: UUID | None = None


class InspectionData(BaseModel):
    id: UUID
    upload_date: datetime
    updated_at: datetime | None = None
    sample_id: UUID | None = None
    picture_set_id: UUID | None = None
    label_info_id: UUID
    product_name: str | None = None
    main_organization_id: UUID | None = None
    main_organization_name: str | None = None
    # verified: bool | None = None


class InspectionUpdate(Inspection):
    pass


class InspectionResponse(InspectionUpdate):
    inspection_id: UUID


class DeletedInspection(DBInspection):
    deleted: bool = True
