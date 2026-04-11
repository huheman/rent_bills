from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
import logging
from uuid import uuid4

from app.clients.feishu_bitable import (
    FIELD_CREATED_AT,
    FIELD_ELECTRICITY_PREV,
    FIELD_ELECTRICITY_PRICE,
    FIELD_ELECTRICITY_THIS,
    FIELD_MONTH,
    FIELD_RENT,
    FIELD_ROOM_NAME,
    FIELD_SPECIAL_ELECTRICITY_PRICE,
    FIELD_SPECIAL_WATER_PRICE,
    FIELD_WATER_PREV,
    FIELD_WATER_PRICE,
    FIELD_WATER_THIS,
    FeishuBitableClient,
)
from app.models.record import Record
from app.schemas.feishu import RenewalResponse
from app.utils.date_utils import format_month_str


logger = logging.getLogger(__name__)


class FeishuRenewalService:
    def __init__(self, client: FeishuBitableClient) -> None:
        self._client = client

    def run(self, target_date: date | None = None) -> RenewalResponse:
        execute_date = target_date or datetime.today().date()
        logger.info(
            "Starting Feishu renewal run target_date=%s",
            execute_date.isoformat(),
        )

        if execute_date.day < 20:
            target_month = format_month_str(execute_date)
            logger.info("Skipping renewal because day is before 20 target_date=%s", execute_date.isoformat())
            return RenewalResponse(
                status="skipped",
                target_month=target_month,
                source_count=0,
                created_count=0,
                results=[f"Skipped because {execute_date.isoformat()} is before the 20th day of the month."],
            )

        month_str = format_month_str(execute_date)
        current_month_records = self._find_by_month(month_str)
        if not current_month_records:
            logger.info("No source records found for month=%s", month_str)
            return RenewalResponse(
                status="completed",
                target_month=month_str,
                source_count=0,
                created_count=0,
                results=["No records found for the target month."],
            )

        next_month_records = [Record.create_from_previous(record) for record in current_month_records]
        results = self._save_records(next_month_records)
        created_count = sum(1 for item in results if item.startswith("Created"))
        logger.info(
            "Finished Feishu renewal target_month=%s source_count=%s created_count=%s",
            month_str,
            len(current_month_records),
            created_count,
        )

        return RenewalResponse(
            status="completed",
            target_month=month_str,
            source_count=len(current_month_records),
            created_count=created_count,
            results=results,
        )

    def _find_by_month(self, month_str: str, room_name: str | None = None) -> list[Record]:
        logger.info("Querying records from Feishu month=%s room_name=%s", month_str, room_name)
        result = self._client.search_by_month(month_str=month_str, room_name=room_name)
        if not result:
            return []

        records: list[Record] = []
        for item in result:
            records.append(
                Record.create_full(
                    room_name=item.get(FIELD_ROOM_NAME, ""),
                    outer_id=item.get("record_id", ""),
                    record_month=_extract_month_text(item.get(FIELD_MONTH)),
                    rent_money=float(item.get(FIELD_RENT, 0.0) or 0.0),
                    water_meter_pre_month=float(item.get(FIELD_WATER_PREV, 0.0) or 0.0),
                    water_meter_this_month=float(item.get(FIELD_WATER_THIS, 0.0) or 0.0),
                    water_price=float(item.get(FIELD_WATER_PRICE, 0.0) or 0.0),
                    electricity_meter_pre_month=float(item.get(FIELD_ELECTRICITY_PREV, 0.0) or 0.0),
                    electricity_meter_this_month=float(item.get(FIELD_ELECTRICITY_THIS, 0.0) or 0.0),
                    electricity_price=float(item.get(FIELD_ELECTRICITY_PRICE, 0.0) or 0.0),
                    special_water_price=_as_optional_float(item.get(FIELD_SPECIAL_WATER_PRICE)),
                    special_electricity_price=_as_optional_float(item.get(FIELD_SPECIAL_ELECTRICITY_PRICE)),
                    created_at=int(item.get(FIELD_CREATED_AT, 0) or 0),
                )
            )
        return records

    def _save_records(self, records: list[Record]) -> list[str]:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self._upsert_record, record) for record in records]
            return [future.result() for future in as_completed(futures)]

    def _upsert_record(self, record: Record) -> str:
        if self._find_by_month(month_str=record.record_month, room_name=record.room_name):
            logger.info("Record already exists record_id=%s", record.id)
            return f"Skipped {record.id}: record already exists."

        to_save = {
            FIELD_ROOM_NAME: record.room_name,
            FIELD_MONTH: record.record_month,
            FIELD_RENT: record.rent_money,
            FIELD_WATER_THIS: record.water_meter_this_month,
            FIELD_WATER_PREV: record.water_meter_pre_month,
            FIELD_ELECTRICITY_PREV: record.electricity_meter_pre_month,
            FIELD_ELECTRICITY_THIS: record.electricity_meter_this_month,
            FIELD_WATER_PRICE: record.water_price,
            FIELD_ELECTRICITY_PRICE: record.electricity_price,
            FIELD_SPECIAL_WATER_PRICE: record.special_water_price,
            FIELD_SPECIAL_ELECTRICITY_PRICE: record.special_electricity_price,
            FIELD_CREATED_AT: record.created_at,
        }
        logger.info("Creating new record record_id=%s record_month=%s", record.id, record.record_month)
        self._client.save_record_to_db(json_record=to_save, request_id=str(uuid4()))
        return f"Created {record.id}."
def _extract_month_text(value: object) -> str:
    if isinstance(value, dict):
        raw_values = value.get("value") or []
        if raw_values:
            return raw_values[0].get("text", "")
    if isinstance(value, str):
        return value
    return ""


def _as_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
