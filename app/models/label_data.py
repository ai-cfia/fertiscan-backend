from pipeline import FertilizerInspection
from pydantic import Field, model_validator


class LabelData(FertilizerInspection):
    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls.model_validate_json(value)
        return value
