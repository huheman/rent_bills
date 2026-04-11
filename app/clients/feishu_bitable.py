import json
from typing import Any

from app.core.config import Settings


FIELD_ROOM_NAME = "房号"
FIELD_MONTH = "月份"
FIELD_RENT = "房租租金(元)"
FIELD_WATER_THIS = "本月水表"
FIELD_WATER_PREV = "上月水表"
FIELD_ELECTRICITY_THIS = "本月电表"
FIELD_ELECTRICITY_PREV = "上月电表"
FIELD_WATER_PRICE = "水费单价"
FIELD_ELECTRICITY_PRICE = "电费单价"
FIELD_SPECIAL_WATER_PRICE = "特殊水费单价"
FIELD_SPECIAL_ELECTRICITY_PRICE = "特殊电费单价"
FIELD_CREATED_AT = "创建时间"


class FeishuBitableClient:
    def __init__(self, settings: Settings) -> None:
        import lark_oapi as lark

        self._settings = settings
        self._client = (
            lark.Client.builder()
            .app_id(settings.feishu_app_id)
            .app_secret(settings.feishu_app_secret)
            .log_level(lark.LogLevel.INFO)
            .build()
        )

    def search_by_month(self, month_str: str, room_name: str | None = None) -> list[dict[str, Any]]:
        from lark_oapi.api.bitable.v1 import Condition, FilterInfo, SearchAppTableRecordRequest
        from lark_oapi.api.bitable.v1 import SearchAppTableRecordRequestBody, Sort

        conditions = [
            Condition.builder().field_name(FIELD_MONTH).operator("is").value([month_str]).build()
        ]
        if room_name and room_name.strip():
            conditions.append(
                Condition.builder().field_name(FIELD_ROOM_NAME).operator("is").value([room_name]).build()
            )

        request_body = (
            SearchAppTableRecordRequestBody.builder()
            .field_names(
                [
                    FIELD_ROOM_NAME,
                    FIELD_MONTH,
                    FIELD_RENT,
                    FIELD_WATER_THIS,
                    FIELD_WATER_PREV,
                    FIELD_ELECTRICITY_THIS,
                    FIELD_ELECTRICITY_PREV,
                    FIELD_WATER_PRICE,
                    FIELD_ELECTRICITY_PRICE,
                    FIELD_SPECIAL_WATER_PRICE,
                    FIELD_SPECIAL_ELECTRICITY_PRICE,
                    FIELD_CREATED_AT,
                ]
            )
            .sort([Sort.builder().field_name(FIELD_ROOM_NAME).desc(True).build()])
            .filter(FilterInfo.builder().conjunction("and").conditions(conditions).build())
            .automatic_fields(False)
            .build()
        )

        items: list[Any] = []
        page_token: str | None = None
        while True:
            request_builder = (
                SearchAppTableRecordRequest.builder()
                .app_token(self._settings.feishu_table_app_token)
                .table_id(self._settings.feishu_table_id)
                .page_size(200)
                .request_body(request_body)
            )
            if page_token:
                request_builder.page_token(page_token)

            response = self._client.bitable.v1.app_table_record.search(request_builder.build())
            if not response.success():
                self._raise_lark_error("search", response)

            items.extend(response.data.items or [])
            if not response.data.has_more:
                break
            page_token = response.data.page_token
            if not page_token:
                raise RuntimeError("Feishu bitable search returned has_more without page_token")

        return self._extract_fields(items)

    def save_record_to_db(self, json_record: dict[str, Any], request_id: str) -> None:
        from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest

        request = (
            CreateAppTableRecordRequest.builder()
            .app_token(self._settings.feishu_table_app_token)
            .table_id(self._settings.feishu_table_id)
            .user_id_type("open_id")
            .client_token(request_id)
            .ignore_consistency_check(True)
            .request_body(AppTableRecord.builder().fields(json_record).build())
            .build()
        )

        response = self._client.bitable.v1.app_table_record.create(request)
        if not response.success():
            self._raise_lark_error("create", response)

    @staticmethod
    def _extract_fields(items: list[Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for item in items:
            fields = item.fields
            if not fields:
                continue

            processed: dict[str, Any] = {
                "record_id": item.record_id,
                FIELD_ROOM_NAME: _extract_text(fields.get(FIELD_ROOM_NAME)),
                FIELD_MONTH: fields.get(FIELD_MONTH),
                FIELD_CREATED_AT: fields.get(FIELD_CREATED_AT, 0),
                FIELD_RENT: fields.get(FIELD_RENT, 0.0),
                FIELD_WATER_THIS: fields.get(FIELD_WATER_THIS, 0.0),
                FIELD_WATER_PREV: fields.get(FIELD_WATER_PREV, 0.0),
                FIELD_ELECTRICITY_THIS: fields.get(FIELD_ELECTRICITY_THIS, 0.0),
                FIELD_ELECTRICITY_PREV: fields.get(FIELD_ELECTRICITY_PREV, 0.0),
                FIELD_WATER_PRICE: _extract_number(fields.get(FIELD_WATER_PRICE)),
                FIELD_ELECTRICITY_PRICE: _extract_number(fields.get(FIELD_ELECTRICITY_PRICE)),
                FIELD_SPECIAL_WATER_PRICE: _extract_number(fields.get(FIELD_SPECIAL_WATER_PRICE)),
                FIELD_SPECIAL_ELECTRICITY_PRICE: _extract_number(fields.get(FIELD_SPECIAL_ELECTRICITY_PRICE)),
            }
            results.append(processed)

        return results

    @staticmethod
    def _raise_lark_error(action: str, response: Any) -> None:
        detail = json.dumps(json.loads(response.raw.content), indent=2, ensure_ascii=False)
        raise RuntimeError(
            f"Feishu bitable {action} failed: code={response.code}, msg={response.msg}, "
            f"log_id={response.get_log_id()}, detail={detail}"
        )


def _extract_text(field_value: Any) -> str:
    if isinstance(field_value, list) and field_value:
        return field_value[0].get("text", "")
    return ""


def _extract_number(field_value: Any) -> float | None:
    if isinstance(field_value, dict):
        values = field_value.get("value") or []
        if values:
            return values[0]
    if isinstance(field_value, (float, int)):
        return float(field_value)
    return None
