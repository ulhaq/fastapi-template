from typing import Annotated

from pydantic import EmailStr, Field, StringConstraints

ConstrainedEmail = Annotated[EmailStr, StringConstraints(to_lower=True)]
Password = Annotated[str, Field(min_length=8)]
NonEmptyStr = Annotated[str, Field(min_length=1)]
