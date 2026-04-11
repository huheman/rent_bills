from fastapi import APIRouter, Depends

from app.api.deps import get_electricity_meter_ocr_service
from app.schemas.common import ApiResponse, success_response
from app.schemas.electricity_meter import ElectricityMeterOcrRequest, ElectricityMeterOcrResponse
from app.services.electricity_meter_ocr import ElectricityMeterOcrService


router = APIRouter(prefix="/electricity-meter", tags=["electricity-meter"])


@router.post("/ocr", response_model=ApiResponse[ElectricityMeterOcrResponse])
def ocr_electricity_meter(
    payload: ElectricityMeterOcrRequest,
    service: ElectricityMeterOcrService = Depends(get_electricity_meter_ocr_service),
) -> ApiResponse[ElectricityMeterOcrResponse]:
    return success_response(service.run(payload))
