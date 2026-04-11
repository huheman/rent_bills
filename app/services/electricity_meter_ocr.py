from app.clients.openai_client import OpenAIClient
from app.schemas.electricity_meter import ElectricityMeterOcrRequest, ElectricityMeterOcrResponse
from app.services.upload import UploadService


OCR_PROMPT = (
    "请严格只根据图片内容做 OCR，不要参考历史数据，不要猜测，不要补全。\n\n"
    "任务：\n"
    "1. 识别图片中的每个数据列。\n"
    "2. 每列顶部有中文数字标题，例如：二、三、四、五。\n"
    "3. 请把列标题转换成阿拉伯数字字符串作为 key，例如：二->\"2\"，三->\"3\"，四->\"4\"，五->\"5\"。\n"
    "4. 每列下面每一行的格式通常是：前面一个序号（1~11），后面一个电表读数。\n"
    "5. 请读取每一行的原始内容 raw，并从中去掉前面的序号，只保留后面的电表读数 value。\n"
    "6. 每列中的结果按图片里从上到下的顺序输出。\n"
    "7. 忽略日期、页眉 NOTE BOOK、无关字迹。\n"
    "8. 如果某一行无法确认，value 填 null，但尽量保留 raw。\n"
    "9. 只返回 JSON，不要输出解释。\n\n"
    "输出格式示例：\n"
    "{"
    "\"2\": ["
    "{\"raw\": \"1 6189\", \"value\": \"6189\"},"
    "{\"raw\": \"2 3272\", \"value\": \"3272\"}"
    "],"
    "\"3\": ["
    "{\"raw\": \"1 1054\", \"value\": \"1054\"}"
    "]"
    "}"
)


class ElectricityMeterOcrService:
    def __init__(
        self,
        upload_service: UploadService,
        openai_client: OpenAIClient,
    ) -> None:
        self._upload_service = upload_service
        self._openai_client = openai_client

    def run(self, payload: ElectricityMeterOcrRequest) -> ElectricityMeterOcrResponse:
        image_url = self._upload_service.create_presigned_download_url(payload.object_key)
        result = self._openai_client.ocr_to_json(OCR_PROMPT, image_url)

        return ElectricityMeterOcrResponse(
            status="completed",
            object_key=payload.object_key,
            result=result,
        )
