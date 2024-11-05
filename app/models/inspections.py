from datetime import datetime
from uuid import UUID

from fertiscan.db.metadata.inspection import GuaranteedAnalysis, SubLabel
from fertiscan.db.metadata.inspection import (
    OrganizationInformation as DBOrganizationInformation,
)
from fertiscan.db.metadata.inspection import ProductInformation as DBProductInformation
from pydantic import BaseModel, Field


class OrganizationInformation(DBOrganizationInformation):
    id: UUID | None = None


class ProductInformation(DBProductInformation):
    label_id: UUID | None = None
    registration_number: str | None = Field(None, pattern=r"^\d{7}[A-Z]$")


class InspectionData(BaseModel):
    id: UUID
    upload_date: datetime
    updated_at: datetime | None = None
    sample_id: UUID | None = None
    picture_set_id: UUID | None = None
    label_info_id: UUID
    product_name: str | None = None
    manufacturer_info_id: UUID | None = None
    company_info_id: UUID | None = None
    company_name: str | None = None


class InspectionUpdate(BaseModel):
    inspection_comment: str | None = None
    verified: bool | None = False
    company: OrganizationInformation | None = OrganizationInformation()
    manufacturer: OrganizationInformation | None = OrganizationInformation()
    product: ProductInformation
    cautions: SubLabel
    instructions: SubLabel
    guaranteed_analysis: GuaranteedAnalysis


class Inspection(InspectionUpdate):
    inspection_id: UUID
