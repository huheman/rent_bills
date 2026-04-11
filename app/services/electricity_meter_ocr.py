from app.clients.openai_client import OpenAIClient
from app.schemas.electricity_meter import ElectricityMeterOcrRequest, ElectricityMeterOcrResponse
from app.services.upload import UploadService


OCR_PROMPT = (
    "请严格只做第一步 OCR：从图片中读取每一列里出现的数字，不要推断房号，不要参考历史数据，不要补全。\n\n"
    "要求：\n"
    "1. 只识别图片里真实可见的数字。\n"
    "2. 每一列输出为一个数组，数组中的元素按“从上到下”的顺序排列。\n"
    "3. 最右边一列命名为 right_1，右边第二列命名为 right_2，右边第三列命名为 right_3，右边第四列命名为 right_4。\n"
    "4. 不要把这些数字映射成房号，这一步只返回每列原始数字。\n"
    "5. 如果某个数字看不清，请保留你看到的内容；如果完全无法辨认，填 null。\n"
    "6. 不允许根据规律猜测，不允许根据上下文补数字，不允许伪造。\n"
    "7. 只返回 JSON，不要输出解释。\n\n"
    "输出格式示例：\n"
    "{\n"
    '  "right_1": [6189, 3255, 6404, null],\n'
    '  "right_2": [1043, 6787, 2435],\n'
    '  "right_3": [4118, 1733],\n'
    '  "right_4": [1817, 1061]\n'
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
