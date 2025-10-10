from typing import Optional
from pydantic import BaseModel, Field

class MoveInOutput(BaseModel):
    name: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    before_address: Optional[str] = Field(default=None)
    after_address: Optional[str] = Field(default=None)