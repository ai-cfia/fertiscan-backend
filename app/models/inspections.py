from datetime import datetime

from fertiscan.db.metadata.inspection import Inspection as DatastoreInspection
from pydantic import UUID4, BaseModel


class InspectionData(BaseModel):
    id: UUID4
    upload_date: datetime
    updated_at: datetime | None = None
    sample_id: UUID4 | None = None
    picture_set_id: UUID4 | None = None
    label_info_id: UUID4
    product_name: str | None = None
    manufacturer_info_id: UUID4 | None = None
    company_info_id: UUID4 | None = None
    company_name: str | None = None


class Inspection(DatastoreInspection):
    inspection_id: UUID4
