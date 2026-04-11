from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)


class PresignUploadResponse(BaseModel):
    method: str
    upload_url: str
    object_key: str
    expires_in: int
    required_headers: dict[str, str]
