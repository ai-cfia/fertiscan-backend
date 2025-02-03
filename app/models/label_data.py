import re
from pipeline import FertilizerInspection
from pydantic import model_validator


class LabelData(FertilizerInspection):
    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls.model_validate_json(value)
        return value
    
    @model_validator(mode="before")
    @classmethod
    def validate_registration_number(cls, value):
        if value is not None:
            inspection = FertilizerInspection.model_validate(value)
            for registration_number in inspection.registration_number:
                if registration_number.identifier is not None:
                    if not re.match(r"\d+(\.\d+)?", registration_number.identifier):
                        raise ValueError(f"Invalid registration number: {registration_number.identifier}")
        return value
