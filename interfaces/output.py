from typing import Optional
from pydantic import BaseModel, Field

class Output(BaseModel):
    status_code: Optional[int] = Field(default=None)
    step_name: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None)