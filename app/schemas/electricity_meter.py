from typing import Any

from pydantic import BaseModel, Field


class ElectricityMeterOcrRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    object_key: str = Field(min_length=1)


class ElectricityMeterOcrResponse(BaseModel):
    status: str
    month: str
    feishu_month: str
    source_count: int
    object_key: str
    result: dict[str, Any] | None
    reason: str | None = None
