from app.clients.openai_client import OpenAIClient
from app.schemas.electricity_meter import ElectricityMeterOcrRequest, ElectricityMeterOcrResponse
from app.services.upload import UploadService


OCR_PROMPT = (
    "请严格只根据图片内容做 OCR，不要参考历史数据，不要猜测，不要补全。\n\n"
    "任务：\n"
    "1. 识别图片中的多个竖列数据。\n"
    "2. 每一列最上方都有一个中文数字标题，例如：二、三、四、五。\n"
    "3. 请把这个中文数字标题转换成阿拉伯数字字符串，作为 JSON 的 key，例如：二->\"2\"，三->\"3\"，四->\"4\"，五->\"5\"。\n"
    "4. 每一列下面有多行数据，每一行的最前面是序号（通常是 1 到 11），序号后面的数字才是真正的电表读数。\n"
    "5. 请忽略每一行前面的序号，只保留后面的电表读数。\n"
    "6. 每列中的读数按图片里从上到下的顺序放入数组。\n"
    "7. 忽略与结果无关的内容，例如日期、页眉 NOTE BOOK、涂改痕迹、无关笔画。\n"
    "8. 如果某一行读数实在无法确认，填 null，不要猜测。\n"
    "9. 只返回 JSON，不要输出解释、不要加 markdown 代码块。\n\n"
    "补充说明：\n"
    "- 每一行形如：\"1 1883\"，其中前面的 1 是序号，不要保留，结果应为 \"1883\"。\n"
    "- 每一行形如：\"10 8650\"，其中前面的 10 是序号，不要保留，结果应为 \"8650\"。\n"
    "- 返回的 value 一律使用字符串数组，避免 OCR 数字处理出错。\n\n"
    "输出格式示例：\n"
    "{\"2\": [\"6189\", \"3255\"], \"3\": [\"1043\", \"6787\"], \"4\": [\"4153\", \"1740\"], \"5\": [\"1883\", \"1123\"]}"
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
