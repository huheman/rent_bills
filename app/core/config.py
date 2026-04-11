from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv
import pytz


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    feishu_app_id: str | None
    feishu_app_secret: str | None
    feishu_table_id: str | None
    feishu_table_app_token: str | None
    app_timezone: str
    oss_access_key_id: str | None
    oss_access_key_secret: str | None
    oss_endpoint: str | None
    oss_bucket_name: str | None
    oss_upload_prefix: str
    oss_presign_expire_seconds: int
    openai_base_url: str | None
    openai_token: str | None
    openai_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        app_timezone = os.getenv("APP_TIMEZONE", "Asia/Shanghai")
        pytz.timezone(app_timezone)
        return cls(
            feishu_app_id=os.getenv("FEISHU_APP_ID"),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET"),
            feishu_table_id=os.getenv("FEISHU_TABLE_ID"),
            feishu_table_app_token=os.getenv("FEISHU_TABLE_APP_TOKEN"),
            app_timezone=app_timezone,
            oss_access_key_id=os.getenv("OSS_ACCESS_KEY_ID"),
            oss_access_key_secret=os.getenv("OSS_ACCESS_KEY_SECRET"),
            oss_endpoint=os.getenv("OSS_ENDPOINT"),
            oss_bucket_name=os.getenv("OSS_BUCKET_NAME"),
            oss_upload_prefix=os.getenv("OSS_UPLOAD_PREFIX", "raw/"),
            oss_presign_expire_seconds=_read_int_env("OSS_PRESIGN_EXPIRE_SECONDS", 600),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_token=os.getenv("OPENAI_TOKEN"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        )

    def require_feishu(self) -> None:
        _require_fields(
            {
                "FEISHU_APP_ID": self.feishu_app_id,
                "FEISHU_APP_SECRET": self.feishu_app_secret,
                "FEISHU_TABLE_ID": self.feishu_table_id,
                "FEISHU_TABLE_APP_TOKEN": self.feishu_table_app_token,
            }
        )

    def require_oss(self) -> None:
        _require_fields(
            {
                "OSS_ACCESS_KEY_ID": self.oss_access_key_id,
                "OSS_ACCESS_KEY_SECRET": self.oss_access_key_secret,
                "OSS_ENDPOINT": self.oss_endpoint,
                "OSS_BUCKET_NAME": self.oss_bucket_name,
            }
        )
        if self.oss_presign_expire_seconds <= 0:
            raise RuntimeError("Environment variable OSS_PRESIGN_EXPIRE_SECONDS must be greater than 0")

    def require_openai(self) -> None:
        _require_fields(
            {
                "OPENAI_BASE_URL": self.openai_base_url,
                "OPENAI_TOKEN": self.openai_token,
                "OPENAI_MODEL": self.openai_model,
            }
        )


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def _require_fields(fields: dict[str, str | None]) -> None:
    missing = [name for name, value in fields.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variable: {', '.join(missing)}")
