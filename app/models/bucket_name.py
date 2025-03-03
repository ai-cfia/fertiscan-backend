from typing import Annotated

from minio.helpers import check_bucket_name
from pydantic import functional_validators


def validate_minio_bucket_name(name: str) -> str:
    check_bucket_name(name, True, True)
    return name


MinioBucketName = Annotated[
    str, functional_validators.AfterValidator(validate_minio_bucket_name)
]
