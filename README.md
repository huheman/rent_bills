# FastAPI Backend

## Quick start

```powershell
cd back_end
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Feishu renewal API

The backend now auto-loads `back_end/.env` via `python-dotenv`.

Fill `back_end/.env` with your real values:

```powershell
APP_TIMEZONE=Asia/Shanghai
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_TABLE_ID=your_table_id
FEISHU_TABLE_APP_TOKEN=your_table_app_token
OSS_ACCESS_KEY_ID=your_ram_user_access_key_id
OSS_ACCESS_KEY_SECRET=your_ram_user_access_key_secret
OSS_ENDPOINT=https://oss-cn-shenzhen.aliyuncs.com
OSS_BUCKET_NAME=your_data_bucket_name
OSS_UPLOAD_PREFIX=raw/
OSS_PRESIGN_EXPIRE_SECONDS=600
```

`.env.example` is kept as a template; `.env` is the local runtime file.

Logs are printed to the terminal by the standard Python `logging` module. There is no file logger in the current setup.

## Docker

Build image:

```powershell
docker build -t serverless-rent-backend .
```

Run container:

```powershell
docker run --rm -p 8000:8000 --env-file .env serverless-rent-backend
```

Or use docker-compose:

```powershell
docker compose up --build
```

Example request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/feishu/renew-records" `
  -ContentType "application/json" `
  -Body '{"target_date":"2026-04-20"}'
```

Presign upload request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/uploads/presign" `
  -ContentType "application/json" `
  -Body '{"filename":"rent-bill.png","content_type":"image/png"}'
```

The API returns a `PUT` URL, the generated `object_key`, and the `required_headers` that the frontend must send back to OSS unchanged.

Successful responses now use a unified envelope:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "completed",
    "target_month": "2026年4月",
    "source_count": 2,
    "created_count": 2,
    "results": ["Created A101@2026年5月."]
  }
}
```

Errors also return JSON with the same top-level shape.

Renewal rule:

- Before the 20th day of the month: return `skipped`
- On or after the 20th day of the month: execute the renewal flow
- Repeated calls after the 20th are safe because record creation is idempotent at the business layer

## Run tests

```powershell
cd back_end
.\.venv\Scripts\Activate.ps1
pytest
```
