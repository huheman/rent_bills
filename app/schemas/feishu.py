from datetime import date

from pydantic import BaseModel, Field


class RenewalRequest(BaseModel):
    target_date: date | None = Field(
        default=None,
        description="续租逻辑参考日期，默认使用今天。",
    )


class RenewalResponse(BaseModel):
    status: str
    target_month: str
    source_count: int
    created_count: int
    results: list[str]
