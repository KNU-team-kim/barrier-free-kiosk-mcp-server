from typing import Optional
from pydantic import BaseModel, Field

class MoveInOutput(BaseModel):
    name: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    before_sido: Optional[str] = Field(default=None)
    before_sigungu: Optional[str] = Field(default=None)
    after_sido: Optional[str] = Field(default=None)
    after_sigungu: Optional[str] = Field(default=None)
    after_road_name: Optional[str] = Field(default=None)
    after_building_number: Optional[str] = Field(default=None)
    after_detail_address: Optional[str] = Field(default=None)