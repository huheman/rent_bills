import json
import logging
from typing import Any

from app.core.config import Settings


logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openai_token,
            base_url=settings.openai_base_url,
        )

    def ocr_to_json(self, prompt: str, s3_image_url: str) -> dict[str, Any]:
        normalized_prompt = prompt.strip()
        normalized_image_url = s3_image_url.strip()
        if not normalized_prompt:
            raise ValueError("prompt cannot be empty")
        if not normalized_image_url:
            raise ValueError("s3_image_url cannot be empty")

        logger.info(
            "Calling OpenAI OCR model=%s prompt=%s image_url=%s",
            self._settings.openai_model,
            normalized_prompt,
            normalized_image_url,
        )

        response = self._client.chat.completions.create(
            model=self._settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an OCR extraction assistant. Read the image and return only "
                        "valid JSON that follows the user's requested structure. Do not wrap "
                        "the JSON in markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{normalized_prompt}\n\nReturn valid JSON only.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": normalized_image_url},
                        },
                    ],
                },
            ],
        )

        content = response.choices[0].message.content
        logger.info("OpenAI OCR raw response=%s", content)
        if not content:
            raise RuntimeError("OpenAI OCR response is empty")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI OCR response is not valid JSON: {content}") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI OCR response JSON must be an object")
        return parsed
