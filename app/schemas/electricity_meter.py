from typing import Any

from pydantic import BaseModel, Field


class ElectricityMeterOcrRequest(BaseModel):
    object_key: str = Field(min_length=1)


class ElectricityMeterOcrResponse(BaseModel):
    status: str
    object_key: str
    result: dict[str, Any] | None
    reason: str | None = None
