import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(RuntimeError)
    async def handle_runtime_error(_: Request, exc: RuntimeError) -> JSONResponse:
        logger.exception("Unhandled runtime error")
        return JSONResponse(
            status_code=500,
            content={
                "code": 5000,
                "message": str(exc),
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "code": 5001,
                "message": "Internal server error",
                "data": None,
            },
        )
