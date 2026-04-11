from fastapi import FastAPI

from app.core.logging import setup_logging
from app.core.handlers import register_exception_handlers
from app.api.routes import feishu, upload
from app.schemas.common import ApiResponse, success_response

setup_logging()


app = FastAPI(
    title="Serverless Rent API",
    version="0.2.0",
)

register_exception_handlers(app)
app.include_router(feishu.router)
app.include_router(upload.router)


@app.get("/", response_model=ApiResponse[dict[str, str]])
async def read_root() -> ApiResponse[dict[str, str]]:
    return success_response({"message": "Serverless Rent API is running."})


@app.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    return success_response({"status": "ok"})
