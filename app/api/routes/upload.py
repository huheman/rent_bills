from fastapi import APIRouter, Depends

from app.api.deps import get_upload_service
from app.schemas.common import ApiResponse, success_response
from app.schemas.upload import PresignUploadRequest, PresignUploadResponse
from app.services.upload import UploadService


router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presign", response_model=ApiResponse[PresignUploadResponse])
def create_presigned_upload(
    payload: PresignUploadRequest,
    service: UploadService = Depends(get_upload_service),
) -> ApiResponse[PresignUploadResponse]:
    return success_response(service.create_presigned_upload(payload))
