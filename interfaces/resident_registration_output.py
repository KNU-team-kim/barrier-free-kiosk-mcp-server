from typing import Optional
from pydantic import BaseModel, Field

class ResidentRegistrationOutput(BaseModel):
    registration_number: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    number: Optional[str] = Field(default=None)