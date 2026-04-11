from app.clients.feishu_bitable import FIELD_ELECTRICITY_PREV, FIELD_ROOM_NAME
from app.schemas.electricity_meter import ElectricityMeterOcrRequest
from app.services.electricity_meter_ocr import ElectricityMeterOcrService


def test_electricity_meter_ocr_skips_when_target_month_has_no_records() -> None:
    class StubFeishuClient:
        def search_by_month(self, month_str, room_name=None):
            assert month_str == "2026年4月"
            assert room_name is None
            return []

    class FailingUploadService:
        def create_presigned_download_url(self, object_key):
            raise AssertionError("should not presign when Feishu has no records")

    class FailingOpenAIClient:
        def ocr_to_json(self, prompt, s3_image_url):
            raise AssertionError("should not call OpenAI when Feishu has no records")

    service = ElectricityMeterOcrService(
        StubFeishuClient(),
        FailingUploadService(),
        FailingOpenAIClient(),
    )

    response = service.run(
        ElectricityMeterOcrRequest(month="2026-04", object_key="raw/2026-04/meter.png")
    )

    assert response.status == "skipped"
    assert response.month == "2026-04"
    assert response.feishu_month == "2026年4月"
    assert response.source_count == 0
    assert response.result is None


def test_electricity_meter_ocr_uses_previous_readings_and_presigned_url() -> None:
    captured = {}

    class StubFeishuClient:
        def search_by_month(self, month_str, room_name=None):
            captured["month_str"] = month_str
            return [
                {FIELD_ROOM_NAME: "201", FIELD_ELECTRICITY_PREV: 1452},
                {FIELD_ROOM_NAME: "202", FIELD_ELECTRICITY_PREV: 2345},
            ]

    class StubUploadService:
        def create_presigned_download_url(self, object_key):
            captured["object_key"] = object_key
            return "https://oss.example.com/raw/2026-04/meter.png?signature=abc"

    class StubOpenAIClient:
        def ocr_to_json(self, prompt, s3_image_url):
            captured["prompt"] = prompt
            captured["image_url"] = s3_image_url
            return {"201": 1460, "202": 2360}

    service = ElectricityMeterOcrService(
        StubFeishuClient(),
        StubUploadService(),
        StubOpenAIClient(),
    )

    response = service.run(
        ElectricityMeterOcrRequest(month="2026-04", object_key="raw/2026-04/meter.png")
    )

    assert response.status == "completed"
    assert response.source_count == 2
    assert response.result == {"201": 1460, "202": 2360}
    assert captured["month_str"] == "2026年4月"
    assert captured["object_key"] == "raw/2026-04/meter.png"
    assert captured["image_url"] == "https://oss.example.com/raw/2026-04/meter.png?signature=abc"
    assert "201: 1452" in captured["prompt"]
    assert "202: 2345" in captured["prompt"]
    assert "key 是房号" in captured["prompt"]


def test_electricity_meter_ocr_appends_extra_prompt_when_provided() -> None:
    captured = {}

    class StubFeishuClient:
        def search_by_month(self, month_str, room_name=None):
            return [{FIELD_ROOM_NAME: "201", FIELD_ELECTRICITY_PREV: 1452}]

    class StubUploadService:
        def create_presigned_download_url(self, object_key):
            return "https://oss.example.com/raw/2026-04/meter.png?signature=abc"

    class StubOpenAIClient:
        def ocr_to_json(self, prompt, s3_image_url):
            captured["prompt"] = prompt
            return {"201": 1460}

    service = ElectricityMeterOcrService(
        StubFeishuClient(),
        StubUploadService(),
        StubOpenAIClient(),
    )

    service.run(
        ElectricityMeterOcrRequest(
            month="2026-04",
            object_key="raw/2026-04/meter.png",
            extra_prompt="201 的数字容易反光，优先看右下角清晰读数。",
        )
    )

    assert "补充要求" in captured["prompt"]
    assert "201 的数字容易反光" in captured["prompt"]
