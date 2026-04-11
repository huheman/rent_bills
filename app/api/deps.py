from fastapi import Depends

from app.clients.feishu_bitable import FeishuBitableClient
from app.clients.openai_client import OpenAIClient
from app.core.config import Settings
from app.services.feishu_renewal import FeishuRenewalService
from app.services.upload import UploadService


def get_settings() -> Settings:
    return Settings.from_env()


def get_feishu_bitable_client(settings: Settings = Depends(get_settings)) -> FeishuBitableClient:
    settings.require_feishu()
    return FeishuBitableClient(settings)


def get_feishu_renewal_service(
    client: FeishuBitableClient = Depends(get_feishu_bitable_client),
) -> FeishuRenewalService:
    return FeishuRenewalService(client)


def get_upload_service(settings: Settings = Depends(get_settings)) -> UploadService:
    settings.require_oss()
    return UploadService(settings)


def get_openai_client(settings: Settings = Depends(get_settings)) -> OpenAIClient:
    settings.require_openai()
    return OpenAIClient(settings)
