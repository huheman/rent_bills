import re
from datetime import datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.exceptions import AppError
from app.schemas.upload import PresignUploadRequest, PresignUploadResponse


_FILENAME_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class UploadService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_presigned_upload(self, payload: PresignUploadRequest) -> PresignUploadResponse:
        object_key = self._build_object_key(payload.filename, payload.month)
        required_headers = {"Content-Type": payload.content_type}

        try:
            import oss2
        except ImportError as exc:
            raise RuntimeError("Missing dependency: oss2") from exc

        auth = oss2.Auth(
            self._settings.oss_access_key_id,
            self._settings.oss_access_key_secret,
        )
        bucket = oss2.Bucket(
            auth,
            self._normalize_endpoint(self._settings.oss_endpoint),
            self._settings.oss_bucket_name,
        )
        upload_url = bucket.sign_url(
            "PUT",
            object_key,
            self._settings.oss_presign_expire_seconds,
            headers=required_headers,
        )

        return PresignUploadResponse(
            method="PUT",
            upload_url=upload_url,
            object_key=object_key,
            expires_in=self._settings.oss_presign_expire_seconds,
            required_headers=required_headers,
        )

    def create_presigned_download_url(self, object_key: str) -> str:
        normalized_object_key = object_key.strip().lstrip("/")
        if not normalized_object_key:
            raise AppError("object_key cannot be empty", code=4003, status_code=400)

        try:
            import oss2
        except ImportError as exc:
            raise RuntimeError("Missing dependency: oss2") from exc

        auth = oss2.Auth(
            self._settings.oss_access_key_id,
            self._settings.oss_access_key_secret,
        )
        bucket = oss2.Bucket(
            auth,
            self._normalize_endpoint(self._settings.oss_endpoint),
            self._settings.oss_bucket_name,
        )
        return bucket.sign_url(
            "GET",
            normalized_object_key,
            self._settings.oss_presign_expire_seconds,
        )

    def _build_object_key(self, filename: str, month: str) -> str:
        safe_filename = self._sanitize_filename(filename)
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        prefix = self._normalize_prefix(self._settings.oss_upload_prefix)
        return f"{prefix}{month}/{timestamp}-{uuid4().hex}-{safe_filename}"

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        candidate = filename.strip()
        if not candidate:
            raise AppError("filename cannot be empty", code=4001, status_code=400)

        candidate = candidate.split("/")[-1].split("\\")[-1]
        candidate = _FILENAME_SAFE_CHARS.sub("-", candidate).strip(".-")
        if not candidate:
            raise AppError("filename is invalid", code=4002, status_code=400)
        return candidate[:255]

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        normalized = prefix.strip("/")
        if not normalized:
            return ""
        return f"{normalized}/"

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"https://{endpoint}"
