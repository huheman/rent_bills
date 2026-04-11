from fastapi.testclient import TestClient

from app.api.deps import get_feishu_renewal_service, get_upload_service
from app.main import app
from app.schemas.feishu import RenewalResponse


client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"message": "Serverless Rent API is running."},
    }


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }


def test_feishu_renew_records() -> None:
    class StubRenewalService:
        def run(self, target_date=None) -> RenewalResponse:
            assert str(target_date) == "2026-04-20"
            return RenewalResponse(
                status="completed",
                target_month="2026年4月",
                source_count=2,
                created_count=2,
                results=["Created A101@2026年5月.", "Created A102@2026年5月."],
            )

    app.dependency_overrides[get_feishu_renewal_service] = lambda: StubRenewalService()
    try:
        response = client.post(
            "/api/feishu/renew-records",
            json={"target_date": "2026-04-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {
            "status": "completed",
            "target_month": "2026年4月",
            "source_count": 2,
            "created_count": 2,
            "results": ["Created A101@2026年5月.", "Created A102@2026年5月."],
        },
    }


def test_feishu_renew_records_runtime_error() -> None:
    class FailingRenewalService:
        def run(self, target_date=None) -> RenewalResponse:
            raise RuntimeError("boom")

    app.dependency_overrides[get_feishu_renewal_service] = lambda: FailingRenewalService()
    try:
        response = client.post(
            "/api/feishu/renew-records",
            json={"target_date": "2026-04-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "code": 5000,
        "message": "boom",
        "data": None,
    }


def test_feishu_renew_records_skips_before_20th() -> None:
    class SkippingRenewalService:
        def run(self, target_date=None) -> RenewalResponse:
            return RenewalResponse(
                status="skipped",
                target_month="2026年4月",
                source_count=0,
                created_count=0,
                results=["Skipped because 2026-04-19 is before the 20th day of the month."],
            )

    app.dependency_overrides[get_feishu_renewal_service] = lambda: SkippingRenewalService()
    try:
        response = client.post(
            "/api/feishu/renew-records",
            json={"target_date": "2026-04-19"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {
            "status": "skipped",
            "target_month": "2026年4月",
            "source_count": 0,
            "created_count": 0,
            "results": ["Skipped because 2026-04-19 is before the 20th day of the month."],
        },
    }


def test_create_presigned_upload() -> None:
    class StubUploadService:
        def create_presigned_upload(self, payload):
            assert payload.filename == "rent-bill.png"
            assert payload.content_type == "image/png"
            return {
                "method": "PUT",
                "upload_url": "https://example.com/upload",
                "object_key": "raw/2026-04/20260410213000-abc-rent-bill.png",
                "expires_in": 600,
                "required_headers": {"Content-Type": "image/png"},
            }

    app.dependency_overrides[get_upload_service] = lambda: StubUploadService()
    try:
        response = client.post(
            "/api/uploads/presign",
            json={"filename": "rent-bill.png", "content_type": "image/png"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {
            "method": "PUT",
            "upload_url": "https://example.com/upload",
            "object_key": "raw/2026-04/20260410213000-abc-rent-bill.png",
            "expires_in": 600,
            "required_headers": {"Content-Type": "image/png"},
        },
    }


def test_create_presigned_upload_rejects_invalid_filename() -> None:
    class FailingUploadService:
        def create_presigned_upload(self, payload):
            raise RuntimeError("should not be called")

    app.dependency_overrides[get_upload_service] = lambda: FailingUploadService()
    try:
        response = client.post(
            "/api/uploads/presign",
            json={"filename": "", "content_type": "image/png"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
