from fastapi import APIRouter, Depends

from app.api.deps import get_feishu_renewal_service
from app.schemas.common import ApiResponse, success_response
from app.schemas.feishu import RenewalRequest, RenewalResponse
from app.services.feishu_renewal import FeishuRenewalService


router = APIRouter(prefix="/feishu", tags=["feishu"])


@router.post("/renew-records", response_model=ApiResponse[RenewalResponse])
def renew_records(
    payload: RenewalRequest,
    service: FeishuRenewalService = Depends(get_feishu_renewal_service),
) -> ApiResponse[RenewalResponse]:
    result = service.run(
        target_date=payload.target_date,
    )
    return success_response(result)
