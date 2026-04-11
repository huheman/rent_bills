from types import SimpleNamespace

from app.clients.openai_client import OpenAIClient
from app.core.config import Settings


def test_openai_client_ocr_to_json(monkeypatch) -> None:
    captured = {}

    class FakeChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"room":"A101","water":12.5}')
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, api_key, base_url) -> None:
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = SimpleNamespace(completions=FakeChatCompletions())

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    settings = Settings(
        feishu_app_id=None,
        feishu_app_secret=None,
        feishu_table_id=None,
        feishu_table_app_token=None,
        app_timezone="Asia/Shanghai",
        oss_access_key_id=None,
        oss_access_key_secret=None,
        oss_endpoint=None,
        oss_bucket_name=None,
        oss_upload_prefix="raw/",
        oss_presign_expire_seconds=600,
        openai_base_url="https://example.com/v1",
        openai_token="test-token",
        openai_model="gpt-4o-mini",
    )

    result = OpenAIClient(settings).ocr_to_json(
        "识别水电表并返回房号和读数",
        "https://bucket.s3.amazonaws.com/rent.png",
    )

    assert result == {"room": "A101", "water": 12.5}
    assert captured["api_key"] == "test-token"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["model"] == "gpt-4o-mini"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["messages"][1]["content"][1]["image_url"] == {
        "url": "https://bucket.s3.amazonaws.com/rent.png",
        "detail": "high",
    }
