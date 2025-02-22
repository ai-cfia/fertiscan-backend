from datetime import datetime
from uuid import UUID

from fertiscan.db.metadata.inspection import DBInspection as DBInspectionMetadata
from fertiscan.db.metadata.inspection import Inspection as DBInspection
from fertiscan.db.metadata.inspection import (
    OrganizationInformation as DBOrganizationInformation,
)
from fertiscan.db.metadata.inspection import ProductInformation as DBProductInformation
from fertiscan.db.metadata.inspection import RegistrationNumber as DBRegistrationNumber
from pydantic import BaseModel, Field

from app.models.label_data import LabelData
from app.models.phone_number import CAPhoneNumber


class OrganizationInformation(DBOrganizationInformation):
    id: UUID | None = None
    phone_number: CAPhoneNumber | None = None


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
    verified: bool | None = None


class RegistrationNumbers(DBRegistrationNumber):
    registration_number: str | None = Field(None, pattern=r"^\d{7}[A-Za-z]$")


class ProductInformation(DBProductInformation):
    label_id: UUID | None = None
    npk: str | None = Field(None, pattern=r"^\d+(\.\d+)?-\d+(\.\d+)?-\d+(\.\d+)?$")
    registration_numbers: list[RegistrationNumbers] | None = []


class Inspection(DBInspection):
    inspection_id: UUID | None = None
    inspector_id: UUID | None = None
    organizations: list[OrganizationInformation] | None = []
    product: ProductInformation
    picture_set_id: UUID


class InspectionCreate(LabelData):
    picture_set_id: UUID


class InspectionUpdate(Inspection):
    pass


class InspectionResponse(Inspection):
    inspection_id: UUID


class DeletedInspection(DBInspectionMetadata):
    deleted: bool = True
