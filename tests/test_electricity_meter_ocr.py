from app.schemas.electricity_meter import ElectricityMeterOcrRequest
from app.services.electricity_meter_ocr import ElectricityMeterOcrService


def test_electricity_meter_ocr_uses_image_only_prompt_and_presigned_url() -> None:
    captured = {}

    class StubUploadService:
        def create_presigned_download_url(self, object_key):
            captured["object_key"] = object_key
            return "https://oss.example.com/raw/2026-04/meter.png?signature=abc"

    class StubOpenAIClient:
        def ocr_to_json(self, prompt, s3_image_url):
            captured["prompt"] = prompt
            captured["image_url"] = s3_image_url
            return {
                "right_1": [6189, 3255, 6404, None],
                "right_2": [1043, 6787, 2435],
            }

    service = ElectricityMeterOcrService(
        StubUploadService(),
        StubOpenAIClient(),
    )

    response = service.run(
        ElectricityMeterOcrRequest(
            object_key="raw/2026-04/meter.png",
        )
    )

    assert response.status == "completed"
    assert response.object_key == "raw/2026-04/meter.png"
    assert response.result == {
        "right_1": [6189, 3255, 6404, None],
        "right_2": [1043, 6787, 2435],
    }
    assert captured["object_key"] == "raw/2026-04/meter.png"
    assert captured["image_url"] == "https://oss.example.com/raw/2026-04/meter.png?signature=abc"
    assert "请严格只做第一步 OCR" in captured["prompt"]
    assert "right_1" in captured["prompt"]
    assert "不要参考历史数据" in captured["prompt"]
