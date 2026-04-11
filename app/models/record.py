from dataclasses import dataclass

from app.utils.date_utils import as_local_date, format_month_str, get_next_month_start_timestamp


@dataclass
class Record:
    id: str
    room_name: str
    record_month: str
    rent_money: float
    water_meter_pre_month: float
    water_meter_this_month: float
    water_price: float
    electricity_meter_pre_month: float
    electricity_meter_this_month: float
    electricity_price: float
    special_water_price: float | None
    special_electricity_price: float | None
    created_at: int
    outer_id: str | None = None

    @classmethod
    def create_full(
        cls,
        room_name: str,
        outer_id: str,
        record_month: str,
        rent_money: float,
        water_meter_pre_month: float,
        water_meter_this_month: float,
        water_price: float,
        electricity_meter_pre_month: float,
        electricity_meter_this_month: float,
        electricity_price: float,
        special_water_price: float | None,
        special_electricity_price: float | None,
        created_at: int,
    ) -> "Record":
        return cls(
            id=f"{room_name}@{record_month}",
            outer_id=outer_id,
            room_name=room_name,
            record_month=record_month,
            rent_money=rent_money,
            water_meter_pre_month=water_meter_pre_month,
            water_meter_this_month=water_meter_this_month,
            water_price=water_price,
            electricity_meter_pre_month=electricity_meter_pre_month,
            electricity_meter_this_month=electricity_meter_this_month,
            electricity_price=electricity_price,
            special_water_price=special_water_price,
            special_electricity_price=special_electricity_price,
            created_at=created_at,
        )

    @classmethod
    def create_from_previous(cls, previous_record: "Record") -> "Record":
        next_month_created_at = get_next_month_start_timestamp(previous_record.created_at)
        next_month = format_month_str(as_local_date(next_month_created_at))
        return cls(
            id=f"{previous_record.room_name}@{next_month}",
            room_name=previous_record.room_name,
            record_month=next_month,
            rent_money=previous_record.rent_money,
            water_meter_pre_month=previous_record.water_meter_this_month,
            water_meter_this_month=previous_record.water_meter_this_month,
            water_price=previous_record.water_price,
            electricity_meter_pre_month=previous_record.electricity_meter_this_month,
            electricity_meter_this_month=previous_record.electricity_meter_this_month,
            electricity_price=previous_record.electricity_price,
            special_water_price=previous_record.special_water_price,
            special_electricity_price=previous_record.special_electricity_price,
            created_at=next_month_created_at,
        )
