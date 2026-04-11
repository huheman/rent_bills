from datetime import datetime
from typing import Any

from app.clients.feishu_bitable import (
    FIELD_ELECTRICITY_PREV,
    FIELD_ROOM_NAME,
    FeishuBitableClient,
)
from app.clients.openai_client import OpenAIClient
from app.schemas.electricity_meter import ElectricityMeterOcrRequest, ElectricityMeterOcrResponse
from app.services.upload import UploadService
from app.utils.date_utils import format_month_str


class ElectricityMeterOcrService:
    def __init__(
        self,
        feishu_client: FeishuBitableClient,
        upload_service: UploadService,
        openai_client: OpenAIClient,
    ) -> None:
        self._feishu_client = feishu_client
        self._upload_service = upload_service
        self._openai_client = openai_client

    def run(self, payload: ElectricityMeterOcrRequest) -> ElectricityMeterOcrResponse:
        feishu_month = _to_feishu_month(payload.month)
        records = self._feishu_client.search_by_month(month_str=feishu_month)

        if not records:
            return ElectricityMeterOcrResponse(
                status="skipped",
                month=payload.month,
                feishu_month=feishu_month,
                source_count=0,
                object_key=payload.object_key,
                result=None,
                reason="No Feishu records found for target month.",
            )

        image_url = self._upload_service.create_presigned_download_url(payload.object_key)
        result = self._openai_client.ocr_to_json(
            _build_prompt(records, payload.extra_prompt),
            image_url,
        )

        return ElectricityMeterOcrResponse(
            status="completed",
            month=payload.month,
            feishu_month=feishu_month,
            source_count=len(records),
            object_key=payload.object_key,
            result=result,
        )


def _to_feishu_month(month: str) -> str:
    return format_month_str(datetime.strptime(month, "%Y-%m").date())


def _build_prompt(records: list[dict[str, Any]], extra_prompt: str | None = None) -> str:
    previous_readings = []
    for record in records:
        room_name = str(record.get(FIELD_ROOM_NAME, "")).strip()
        if not room_name:
            continue
        previous_readings.append(
            f"{room_name}: {record.get(FIELD_ELECTRICITY_PREV, 0)}"
        )

    readings_text = "\n".join(previous_readings)
    prompt = (
        "请从图片中识别每个房间的本月电表读数。\n\n"
        "以下是上个月各房间的电表读数，仅用于辅助判断：\n"
        f"{readings_text}\n\n"
        "请只返回 JSON 对象，key 是房号，value 是图片中读取到的本月电表读数。\n"
        "示例：{\"201\": 1460, \"202\": 2360}"
    )
    normalized_extra_prompt = (extra_prompt or "").strip()
    if not normalized_extra_prompt:
        return prompt
    return f"{prompt}\n\n补充要求：\n{normalized_extra_prompt}"
