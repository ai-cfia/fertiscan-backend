from typing import Annotated

import phonenumbers
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

CAPhoneNumber = Annotated[
    str | phonenumbers.PhoneNumber,
    PhoneNumberValidator(
        supported_regions=["US", "CA"],
        number_format="E164",
        default_region="CA",
    ),
]
